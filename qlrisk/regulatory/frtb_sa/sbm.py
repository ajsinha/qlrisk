"""
QLRisk - FRTB SA Sensitivities-Based Method (MAR21)
===================================================

    fs = frtb_sensitivities(sensitivity_result, market_data, reporting_currency="USD",
                            equity_buckets={"SPX": 12}, credit_buckets={"ACME": 4})
    charge = sbm_capital(fs, trades=trades, market_data=market_data)   # incl. curvature
    charge.total, charge.by_component, charge.scenario

Delta and vega charges aggregate weighted sensitivities WS_k = RW_k * s_k:

    K_b = sqrt(max(0, sum_k sum_l rho_kl WS_k WS_l))
    S_b = max(min(sum_k WS_k, K_b), -K_b)
    charge = sqrt(sum_b K_b^2 + sum_{b!=c} gamma_bc S_b S_c)
    (if the radicand is negative, S_b = sum_k WS_k is used instead, then floored at 0)

Curvature (EQ, CM, FX, GIRR, CSR) uses full revaluation under +/- RW shocks:

    CVR_k(+/-) = -sum_i [V_i(x_k +/- RW) - V_i(x_k) -/+ RW * s_ik]

The charge is computed under the low / medium / high correlation scenarios
and the maximum is the SBM capital.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ...riskfactors.mapping import enumerate_risk_factors, get_factor_value
from ...riskfactors.shocks import Shock, ShockType, apply_shocks
from ...riskfactors.taxonomy import FactorKind, RiskClass
from ...sensitivities.engine import _currency_code, fx_convert
from ...sensitivities.ladders import rebucket
from ...sensitivities.measures import SensitivityMeasure
from ...sensitivities.results import SensitivityResult
from . import parameters as p

SCENARIOS = ("low", "medium", "high")


@dataclass
class FRTBSensitivity:
    """One FRTB risk-factor sensitivity s_k with its risk weight."""
    risk_class: str              # GIRR, CSR, EQ, CM, FX
    risk_type: str               # delta, vega
    bucket: Any                  # currency (GIRR, FX) or bucket number
    name: str                    # curve / issuer / ticker / commodity / currency
    tenor: Optional[float]       # vertex (delta) or option maturity (vega)
    sensitivity: float
    risk_weight: float

    @property
    def ws(self) -> float:
        return self.risk_weight * self.sensitivity


@dataclass
class SBMResult:
    total: float
    scenario: str
    by_scenario: Dict[str, float]
    by_component: Dict[Tuple[str, str], float]             # (risk_class, delta|vega|curvature) in chosen scenario
    by_bucket: Dict[Tuple[str, str, Any], float] = field(default_factory=dict)
    skipped_factors: List[str] = field(default_factory=list)


# =============================================================================
# Mapping qlrisk sensitivities to FRTB sensitivities
# =============================================================================

def _girr_rw(ccy: str, tenor: float, reporting: str) -> float:
    rw = p.GIRR_RW[tenor]
    return rw / math.sqrt(2) if ccy in p.GIRR_SPECIFIED_CCY or ccy == reporting else rw


def _eq_small(bucket: int) -> bool:
    return bucket in (9, 10, 11)


def frtb_sensitivities(
    result: SensitivityResult,
    market_data: Any,
    reporting_currency: str = "USD",
    curve_currency: Optional[Mapping[str, str]] = None,
    credit_buckets: Optional[Mapping[str, int]] = None,
    equity_buckets: Optional[Mapping[str, int]] = None,
    commodity_buckets: Optional[Mapping[str, int]] = None,
    vol_underlyings: Optional[Mapping[str, str]] = None,
) -> Tuple[List[FRTBSensitivity], List[str]]:
    """
    Convert a SensitivityResult (computed in `reporting_currency`) into FRTB delta and vega sensitivities.

    Mappings default to: forward-curve index -> parameters.INDEX_CURRENCY; credit names -> bucket 16
    (other sector); equities -> bucket 11 (other); commodities -> parameters.COMMODITY_BUCKET or 11.
    `vol_underlyings` maps a volatility surface name to its underlying ticker / commodity / currency pair /
    curve; by default '<underlying>_vol' is parsed and generic names map to bucket 'other'.

    Returns (sensitivities, skipped factor names).
    """
    ccy_of = {**p.INDEX_CURRENCY, **(curve_currency or {})}
    credit_buckets, equity_buckets = credit_buckets or {}, equity_buckets or {}
    cm_buckets = {**p.COMMODITY_BUCKET, **(commodity_buckets or {})}
    vol_underlyings = vol_underlyings or {}

    value, deriv = {}, {}
    for rec in result.records:
        if rec.factor is None or rec.measure in (SensitivityMeasure.THETA, SensitivityMeasure.CROSS_GAMMA):
            continue
        value[rec.factor] = value.get(rec.factor, 0.0) + rec.value
        deriv[rec.factor] = deriv.get(rec.factor, 0.0) + (rec.derivative or 0.0)

    girr: Dict[Tuple[str, str], Dict[float, float]] = {}
    csr: Dict[str, Dict[float, float]] = {}
    vega: Dict[Tuple[str, Any, str, str], Dict[float, float]] = {}
    out: List[FRTBSensitivity] = []
    skipped: List[str] = []

    for key, v in value.items():
        if key.kind is FactorKind.RATE and key.field in ("discount_curve", "forward_curves", "reference_rates"):
            ccy = reporting_currency if key.field == "discount_curve" else ccy_of.get(key.name, reporting_currency)
            curve = "DISCOUNT" if key.field == "discount_curve" else key.name
            tenor = key.tenor if key.tenor is not None else 0.25
            girr.setdefault((ccy, curve), {})
            girr[(ccy, curve)][tenor] = girr[(ccy, curve)].get(tenor, 0.0) + v / 1e-4
        elif key.field == "credit_curves":
            csr.setdefault(key.name, {})
            csr[key.name][key.tenor or 5.0] = csr[key.name].get(key.tenor or 5.0, 0.0) + v / 1e-4
        elif key.field == "equity_prices":
            b = equity_buckets.get(key.name, p.EQ_OTHER_BUCKET)
            out.append(FRTBSensitivity("EQ", "delta", b, key.name, None, v / 0.01, p.EQ_RW[b]))
        elif key.field == "commodity_prices":
            b = cm_buckets.get(key.name.upper(), p.CM_OTHER_BUCKET)
            out.append(FRTBSensitivity("CM", "delta", b, key.name, None, v / 0.01, p.CM_RW[b]))
        elif key.field == "fx_spots" and key.name and len(key.name) == 6:
            base, quote = key.name[:3], key.name[3:]
            s = v / 0.01
            legs = [(base, s)] if quote == reporting_currency else [(quote, -s)] if base == reporting_currency \
                else [(base, s), (quote, -s)]
            for ccy, sens in legs:
                rw = p.FX_RW / math.sqrt(2) if reporting_currency == "USD" and ccy in p.FX_LIQUID_VS_USD else p.FX_RW
                out.append(FRTBSensitivity("FX", "delta", ccy, ccy, None, sens, rw))
        elif key.kind is FactorKind.VOLATILITY:
            sigma = get_factor_value(market_data, key)
            s = deriv[key] * sigma
            underlying = vol_underlyings.get(key.name) or (key.name[:-4] if key.name.endswith("_vol") else key.name)
            rc = key.risk_class
            if rc is RiskClass.INTEREST_RATE:
                cls, bucket, name, rw = "GIRR", ccy_of.get(underlying.upper(), reporting_currency), key.name, p.vega_rw("IR")
            elif rc is RiskClass.EQUITY:
                b = equity_buckets.get(underlying, p.EQ_OTHER_BUCKET)
                cls, bucket, name, rw = "EQ", b, underlying, p.vega_rw("EQ_SMALL" if _eq_small(b) else "EQ_LARGE")
            elif rc is RiskClass.FX:
                cls, bucket, name, rw = "FX", underlying.upper() if len(underlying) == 6 else "other", key.name, p.vega_rw("FX")
            elif rc is RiskClass.COMMODITY:
                cls, bucket, name, rw = "CM", cm_buckets.get(underlying.upper(), p.CM_OTHER_BUCKET), underlying, p.vega_rw("CM")
            elif rc is RiskClass.CREDIT:
                cls, bucket, name, rw = "CSR", credit_buckets.get(underlying, p.CSR_OTHER_BUCKET), underlying, p.vega_rw("CR")
            else:
                skipped.append(str(key))
                continue
            vega.setdefault((cls, bucket, name, rw), {})
            mat = key.tenor if key.tenor is not None else 1.0
            vega[(cls, bucket, name, rw)][mat] = vega[(cls, bucket, name, rw)].get(mat, 0.0) + s
        else:
            skipped.append(str(key))

    for (ccy, curve), ladder in girr.items():
        for t, s in rebucket(ladder, p.GIRR_VERTICES).items():
            if s:
                out.append(FRTBSensitivity("GIRR", "delta", ccy, curve, t, s, _girr_rw(ccy, t, reporting_currency)))
    for name, ladder in csr.items():
        b = credit_buckets.get(name, p.CSR_OTHER_BUCKET)
        for t, s in rebucket(ladder, p.CSR_VERTICES).items():
            if s:
                out.append(FRTBSensitivity("CSR", "delta", b, name, t, s, p.CSR_RW[b]))
    for (cls, bucket, name, rw), ladder in vega.items():
        for t, s in rebucket(ladder, p.VEGA_MATURITIES).items():
            if s:
                out.append(FRTBSensitivity(cls, "vega", bucket, name, t, s, rw))
    return out, skipped


# =============================================================================
# Correlations
# =============================================================================

def _tenor_rho(a: float, b: float, decay: float) -> float:
    return math.exp(-decay * abs(a - b) / min(a, b))


def _rho(x: FRTBSensitivity, y: FRTBSensitivity) -> float:
    rc = x.risk_class
    if x.risk_type == "vega":
        mat = _tenor_rho(x.tenor, y.tenor, p.VEGA_ALPHA)
        if rc in ("GIRR", "FX"):
            return min(mat, 1.0)
        return min(_name_rho(x, y) * mat, 1.0)
    if rc == "GIRR":
        r = max(_tenor_rho(x.tenor, y.tenor, p.GIRR_THETA), p.GIRR_RHO_FLOOR) if x.tenor != y.tenor else 1.0
        return r if x.name == y.name else r * p.GIRR_DIFFERENT_CURVE
    if rc == "CSR":
        return _name_rho(x, y) * (1.0 if x.tenor == y.tenor else p.CSR_RHO_TENOR)
    return _name_rho(x, y)


def _name_rho(x: FRTBSensitivity, y: FRTBSensitivity) -> float:
    if x.name == y.name:
        return 1.0
    if x.risk_class == "EQ":
        return p.EQ_RHO.get(x.bucket, 0.0)
    if x.risk_class == "CM":
        return p.CM_RHO.get(x.bucket, 0.0)
    if x.risk_class == "CSR":
        return p.CSR_INDEX_RHO_NAME if x.bucket in (17, 18) else p.CSR_RHO_NAME
    return 1.0


def _csr_sector(b: int) -> int:
    return b if b <= 8 else (b - 8 if b <= 15 else b)


def _gamma(rc: str, b: Any, c: Any, csr_sector_gamma: float) -> float:
    if rc == "GIRR":
        return p.GIRR_GAMMA
    if rc == "FX":
        return p.FX_GAMMA
    if rc == "EQ":
        return p.eq_gamma(b, c)
    if rc == "CM":
        return 0.0 if p.CM_OTHER_BUCKET in (b, c) else p.CM_GAMMA
    if rc == "CSR":
        if p.CSR_OTHER_BUCKET in (b, c):
            return 0.0
        both_rated = b <= 15 and c <= 15
        rating = p.CSR_GAMMA_RATING if both_rated and ((b in p.CSR_IG_BUCKETS) != (c in p.CSR_IG_BUCKETS)) else 1.0
        sb, sc = _csr_sector(b), _csr_sector(c)
        if csr_sector_gamma is not None and sb != sc:
            return rating * csr_sector_gamma
        return rating * p.csr_sector_gamma(sb, sc)
    raise ValueError(rc)


def _no_diversification_bucket(rc: str, b: Any) -> bool:
    return (rc == "CSR" and b == p.CSR_OTHER_BUCKET) or (rc == "EQ" and b == p.EQ_OTHER_BUCKET)


# =============================================================================
# Aggregation
# =============================================================================

def _across(rc: str, kb: Dict[Any, float], sums: Dict[Any, float], scenario: str, csr_sector_gamma: float,
            square_gamma: bool = False, psi_rule: bool = False) -> float:
    buckets = list(kb)
    sb = {b: max(min(sums[b], kb[b]), -kb[b]) for b in buckets}

    def radicand(s):
        tot = sum(kb[b] ** 2 for b in buckets)
        for i, b in enumerate(buckets):
            for c in buckets[i + 1:]:
                g = p.scenario_rho(_gamma(rc, b, c, csr_sector_gamma), scenario)
                if square_gamma:
                    g = g * g
                if psi_rule and s[b] < 0 and s[c] < 0:
                    continue
                tot += 2 * g * s[b] * s[c]
        return tot

    r = radicand(sb)
    if r < 0:
        r = radicand(sums)
    return math.sqrt(max(r, 0.0))


def _delta_vega_charge(items: List[FRTBSensitivity], rc: str, scenario: str, csr_sector_gamma: float,
                       by_bucket: Dict) -> float:
    buckets: Dict[Any, List[FRTBSensitivity]] = {}
    for it in items:
        buckets.setdefault(it.bucket, []).append(it)
    kb, sums = {}, {}
    for b, xs in buckets.items():
        ws = np.array([x.ws for x in xs])
        if _no_diversification_bucket(rc, b):
            kb[b] = float(np.abs(ws).sum())
        else:
            n = len(xs)
            corr = np.eye(n)
            for i in range(n):
                for j in range(i + 1, n):
                    corr[i, j] = corr[j, i] = p.scenario_rho(_rho(xs[i], xs[j]), scenario)
            kb[b] = math.sqrt(max(float(ws @ corr @ ws), 0.0))
        sums[b] = float(ws.sum())
        by_bucket[(rc, xs[0].risk_type, b)] = kb[b]
    return _across(rc, kb, sums, scenario, csr_sector_gamma)


# =============================================================================
# Curvature
# =============================================================================

def _portfolio_pv(trades: Sequence[Any], md: Any, ccy: str) -> float:
    total = 0.0
    for t in trades:
        res = t.price(md)
        total += fx_convert(md, float(res.npv), _currency_code(res.currency), ccy)
    return total


def curvature_risk_factors(fs: List[FRTBSensitivity], market_data: Any, reporting_currency: str,
                           curve_currency: Optional[Mapping[str, str]] = None,
                           credit_buckets: Optional[Mapping[str, int]] = None):
    """
    Curvature risk factors: (risk_class, bucket, name, rw, s_total, up_shocks, down_shocks).
    s_total is the summed delta sensitivity the curvature formula subtracts.
    """
    ccy_of = {**p.INDEX_CURRENCY, **(curve_currency or {})}
    keys = enumerate_risk_factors(market_data)
    deltas: Dict[Tuple[str, Any, str], Tuple[float, float]] = {}
    for f in fs:
        if f.risk_type != "delta":
            continue
        if f.risk_class == "GIRR":
            k = ("GIRR", f.bucket, f.bucket)
            rw = p.GIRR_CURVATURE_RW
        else:
            k = (f.risk_class, f.bucket, f.name)
            rw = f.risk_weight if f.risk_class != "FX" else p.FX_RW
        s, _ = deltas.get(k, (0.0, rw))
        deltas[k] = (s + f.sensitivity, rw)

    factors = []
    for (rc, bucket, name), (s_tot, rw) in deltas.items():
        def shocks(sign: float):
            out = []
            for key in keys:
                if rc == "GIRR" and key.kind is FactorKind.RATE and key.field in ("discount_curve", "forward_curves",
                                                                                     "reference_rates"):
                    ccy = reporting_currency if key.field == "discount_curve" else ccy_of.get(key.name, reporting_currency)
                    if ccy == bucket:
                        out.append(Shock(key, sign * rw, ShockType.ABSOLUTE))
                elif rc == "CSR" and key.field == "credit_curves" and key.name == name:
                    out.append(Shock(key, sign * rw, ShockType.ABSOLUTE))
                elif rc == "EQ" and key.field == "equity_prices" and key.name == name:
                    out.append(Shock(key, sign * rw, ShockType.RELATIVE))
                elif rc == "CM" and key.field == "commodity_prices" and key.name == name:
                    out.append(Shock(key, sign * rw, ShockType.RELATIVE))
                elif rc == "FX" and key.field == "fx_spots" and key.name and len(key.name) == 6:
                    base, quote = key.name[:3], key.name[3:]
                    if base == name:
                        out.append(Shock(key, sign * rw, ShockType.RELATIVE))
                    elif quote == name:
                        out.append(Shock(key, 1.0 / (1.0 + sign * rw) - 1.0, ShockType.RELATIVE))
            return out
        factors.append((rc, bucket, name, rw, s_tot, shocks(1.0), shocks(-1.0)))
    return factors


def _curvature_charge(cvr: Dict[str, List[Tuple[Any, str, float, float]]], scenario: str,
                      csr_sector_gamma: float, by_bucket: Dict) -> Dict[str, float]:
    out = {}
    for rc, rows in cvr.items():
        buckets: Dict[Any, List[Tuple[str, float, float]]] = {}
        for bucket, name, up, dn in rows:
            buckets.setdefault(bucket, []).append((name, up, dn))
        kb, sums = {}, {}
        for b, xs in buckets.items():
            def k_of(vals, names):
                tot = sum(max(v, 0.0) ** 2 for v in vals)
                for i in range(len(vals)):
                    for j in range(i + 1, len(vals)):
                        if vals[i] < 0 and vals[j] < 0:
                            continue
                        rho = 1.0 if names[i] == names[j] else _curv_name_rho(rc, b)
                        rho = p.scenario_rho(rho, scenario)
                        tot += 2 * rho * rho * vals[i] * vals[j]
                return math.sqrt(max(tot, 0.0))
            names = [x[0] for x in xs]
            ups, dns = [x[1] for x in xs], [x[2] for x in xs]
            k_up, k_dn = k_of(ups, names), k_of(dns, names)
            if k_up > k_dn or (k_up == k_dn and sum(ups) >= sum(dns)):
                kb[b], sums[b] = k_up, sum(ups)
            else:
                kb[b], sums[b] = k_dn, sum(dns)
            by_bucket[(rc, "curvature", b)] = kb[b]
        out[rc] = _across(rc, kb, sums, scenario, csr_sector_gamma, square_gamma=True, psi_rule=True)
    return out


def _curv_name_rho(rc: str, bucket: Any) -> float:
    if rc == "EQ":
        return p.EQ_RHO.get(bucket, 0.0)
    if rc == "CM":
        return p.CM_RHO.get(bucket, 0.0)
    if rc == "CSR":
        return p.CSR_INDEX_RHO_NAME if bucket in (17, 18) else p.CSR_RHO_NAME
    return 1.0


# =============================================================================
# Total
# =============================================================================

def sbm_capital(
    fs: List[FRTBSensitivity],
    trades: Optional[Sequence[Any]] = None,
    market_data: Any = None,
    reporting_currency: str = "USD",
    curve_currency: Optional[Mapping[str, str]] = None,
    credit_buckets: Optional[Mapping[str, int]] = None,
    csr_sector_gamma: Optional[float] = p.CSR_SECTOR_GAMMA_DEFAULT,
    skipped: Optional[List[str]] = None,
) -> SBMResult:
    """
    SBM capital = max over correlation scenarios of sum(delta + vega + curvature charges).
    Curvature is included when `trades` and `market_data` are given.
    """
    groups: Dict[Tuple[str, str], List[FRTBSensitivity]] = {}
    for f in fs:
        groups.setdefault((f.risk_class, f.risk_type), []).append(f)

    cvr: Dict[str, List[Tuple[Any, str, float, float]]] = {}
    if trades is not None and market_data is not None:
        base = _portfolio_pv(trades, market_data, reporting_currency)
        for rc, bucket, name, rw, s_tot, up, dn in curvature_risk_factors(
                fs, market_data, reporting_currency, curve_currency, credit_buckets):
            if not up:
                continue
            v_up = _portfolio_pv(trades, apply_shocks(market_data, up), reporting_currency)
            v_dn = _portfolio_pv(trades, apply_shocks(market_data, dn), reporting_currency)
            cvr.setdefault(rc, []).append((bucket, name, -(v_up - base - rw * s_tot), -(v_dn - base + rw * s_tot)))

    results = {}
    for scenario in SCENARIOS:
        by_bucket: Dict = {}
        comp = {k: _delta_vega_charge(v, k[0], scenario, csr_sector_gamma, by_bucket) for k, v in groups.items()}
        for rc, val in _curvature_charge(cvr, scenario, csr_sector_gamma, by_bucket).items():
            comp[(rc, "curvature")] = val
        results[scenario] = (sum(comp.values()), comp, by_bucket)
    chosen = max(SCENARIOS, key=lambda s: results[s][0])
    total, comp, by_bucket = results[chosen]
    return SBMResult(total, chosen, {s: results[s][0] for s in SCENARIOS}, comp, by_bucket, list(skipped or []))


__all__ = ["FRTBSensitivity", "SBMResult", "frtb_sensitivities", "sbm_capital", "curvature_risk_factors", "SCENARIOS"]
