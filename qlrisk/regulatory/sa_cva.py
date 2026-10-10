"""
QLRisk - SA-CVA: Standardised Approach for CVA Risk (Basel MAR50.42-77)
=======================================================================

    cva_fn = cva_from_profile(counterparty="ACME", time_grid=grid, expected_exposure=ee)
    result = sa_cva_capital(cva_fn, market_data, counterparty_buckets={"ACME": ("4", True)},
                            hedges=[cds_on_acme])
    result.total, result.by_component

Sensitivities (bump-and-revalue of a CVA function of market data):

    risk class               risk factors (per bucket)                       shift            s =
    IR delta                 specified ccy: 1y, 2y, 5y, 10y, 30y vertices    +1bp absolute    dCVA / 0.0001
                             other ccy: whole curve (parallel)
    FX delta                 each currency vs the reporting currency         +1% relative     dCVA / 0.01
    counterparty CS delta    counterparty curve at 0.5, 1, 3, 5, 10y         +1bp absolute    dCVA / 0.0001
    reference CS delta       all credit curves in the bucket together        +1bp absolute    dCVA / 0.0001
    equity / commodity delta all prices in the bucket together               +1% relative     dCVA / 0.01
    vega (IR, FX, RCS, EQ, CM) all vols of the bucket together               +1% relative     dCVA / 0.01

Hedge sensitivities use the same shifts on the hedges' market value with the sign flipped
(s_hdg = -dMV / shift), so an eligible hedge offsets CVA risk.

Aggregation (MAR50.53), R = 0.01, m_CVA = 1:
    WS_k = RW_k (s_k^CVA + s_k^Hdg)
    K_b  = sqrt( sum_k sum_l rho_kl WS_k WS_l + R sum_k (RW_k s_k^Hdg)^2 )
    K    = m_CVA sqrt( sum_b K_b^2 + sum_{b != c} gamma_bc S_b S_c ),  S_b = max(min(sum_k WS_k, K_b), -K_b)
    capital = sum over risk classes and risk types of K

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ..products.base import curve_value
from ..riskfactors.mapping import enumerate_risk_factors
from ..riskfactors.shocks import Shock, ShockType, apply_shocks
from ..riskfactors.taxonomy import FactorKind, RiskClass, RiskFactorKey
from ..sensitivities.engine import _currency_code, fx_convert
from .frtb_sa.parameters import COMMODITY_BUCKET, INDEX_CURRENCY, eq_gamma

R_HEDGE, M_CVA = 0.01, 1.0

# ---- MAR50.55-57 interest rate
IR_TENORS = (1.0, 2.0, 5.0, 10.0, 30.0)
IR_SPECIFIED = {"USD", "EUR", "GBP", "AUD", "CAD", "SEK", "JPY"}
IR_RW_SPECIFIED = {1.0: 0.0111, 2.0: 0.0093, 5.0: 0.0074, 10.0: 0.0074, 30.0: 0.0074}
IR_RW_OTHER = 0.0158
IR_RHO = {(1.0, 2.0): 0.91, (1.0, 5.0): 0.72, (1.0, 10.0): 0.55, (1.0, 30.0): 0.31, (2.0, 5.0): 0.87,
          (2.0, 10.0): 0.72, (2.0, 30.0): 0.45, (5.0, 10.0): 0.91, (5.0, 30.0): 0.68, (10.0, 30.0): 0.83}
IR_GAMMA, FX_GAMMA = 0.5, 0.6
# ---- MAR50.60-62 FX
FX_RW = 0.11
# ---- MAR50.63-65 counterparty credit spread
CCS_TENORS = (0.5, 1.0, 3.0, 5.0, 10.0)
CCS_RW = {"1a": (0.005, 0.02), "1b": (0.01, 0.04), "2": (0.05, 0.12), "3": (0.03, 0.07), "4": (0.03, 0.085),
          "5": (0.02, 0.055), "6": (0.015, 0.05), "7": (0.05, 0.12), "8": (0.015, 0.05)}
_CCS_GAMMA_ROWS = {1: (1.0, .10, .20, .25, .20, .15, 0.0, .45), 2: (.10, 1.0, .05, .15, .20, .05, 0.0, .45),
                   3: (.20, .05, 1.0, .20, .25, .05, 0.0, .45), 4: (.25, .15, .20, 1.0, .25, .05, 0.0, .45),
                   5: (.20, .20, .25, .25, 1.0, .05, 0.0, .45), 6: (.15, .05, .05, .05, .05, 1.0, 0.0, .45),
                   7: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0), 8: (.45, .45, .45, .45, .45, .45, 0.0, 1.0)}
# ---- MAR50.66-69 reference credit spread (IG 1-7, HY/NR 8-14 same sectors, 15 other, 16 IG index, 17 HY index)
RCS_RW = {1: .005, 2: .01, 3: .05, 4: .03, 5: .03, 6: .02, 7: .015, 8: .02, 9: .04, 10: .12, 11: .07,
          12: .085, 13: .055, 14: .05, 15: .12, 16: .015, 17: .05}
_RCS_SECTOR_GAMMA = {(1, 2): .75, (1, 3): .10, (1, 4): .20, (1, 5): .25, (1, 6): .20, (1, 7): .15,
                     (2, 3): .05, (2, 4): .15, (2, 5): .20, (2, 6): .15, (2, 7): .10, (3, 4): .05, (3, 5): .15,
                     (3, 6): .20, (3, 7): .05, (4, 5): .20, (4, 6): .25, (4, 7): .05, (5, 6): .25, (5, 7): .05,
                     (6, 7): .05}
# ---- MAR50.70-77 equity, commodity
EQ_RW = {1: .55, 2: .60, 3: .45, 4: .55, 5: .30, 6: .35, 7: .40, 8: .50, 9: .70, 10: .50, 11: .70, 12: .15, 13: .25}
CM_RW = {1: .30, 2: .35, 3: .60, 4: .80, 5: .40, 6: .45, 7: .20, 8: .35, 9: .25, 10: .35, 11: .50}
VEGA_RW_DEFAULT, VEGA_RW_EQ_LARGE = 1.0, 0.78


@dataclass
class CVASensitivity:
    risk_class: str              # IR, FX, CCS, RCS, EQ, CM
    risk_type: str               # delta, vega
    bucket: Any
    factor: Any                  # tenor, name or None (one factor per bucket)
    s_cva: float
    s_hdg: float
    rw: float
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def ws(self) -> float:
        return self.rw * (self.s_cva + self.s_hdg)


@dataclass
class SACVAResult:
    total: float
    by_component: Dict[Tuple[str, str], float]
    by_bucket: Dict[Tuple[str, str, Any], float]
    sensitivities: List[CVASensitivity]


# =============================================================================
# CVA functions
# =============================================================================

def cva_from_profile(counterparty: str, time_grid: Sequence[float], expected_exposure: Sequence[float],
                     recovery: float = 0.4) -> Callable[[Any], float]:
    """
    CVA(md) = (1 - R) sum_i EE(t_i) [S(t_{i-1}) - S(t_i)] DF(t_i),  S(t) = exp(-s(t) t / (1 - R)),
    with the counterparty spread s(t) from md.credit_curves[counterparty] and DF from md.discount_curve.
    The exposure profile is held fixed, so it carries credit and discounting sensitivities only; pass
    your own callable to capture exposure sensitivities too.
    """
    grid, ee = np.asarray(time_grid, float), np.asarray(expected_exposure, float)

    def cva(md: Any) -> float:
        curve = md.credit_curves[counterparty]
        surv_prev, total = 1.0, 0.0
        for t, e in zip(grid, ee):
            surv = math.exp(-curve_value(curve, t, 0.0) * t / (1 - recovery))
            total += e * (surv_prev - surv) * math.exp(-curve_value(md.discount_curve, t) * t)
            surv_prev = surv
        return (1 - recovery) * total
    return cva


# =============================================================================
# Sensitivities
# =============================================================================

def _hat(vertices: Sequence[float], k: int) -> Callable[[float], float]:
    """Piecewise-linear weight that is 1 at vertex k and 0 at its neighbours (flat beyond the ends)."""
    v = list(vertices)
    def w(t: float) -> float:
        if t <= v[0]:
            return 1.0 if k == 0 else 0.0
        if t >= v[-1]:
            return 1.0 if k == len(v) - 1 else 0.0
        if k > 0 and v[k - 1] <= t <= v[k]:
            return (t - v[k - 1]) / (v[k] - v[k - 1])
        if k < len(v) - 1 and v[k] <= t <= v[k + 1]:
            return (v[k + 1] - t) / (v[k + 1] - v[k])
        return 0.0
    return w


def sa_cva_sensitivities(
    cva_fn: Callable[[Any], float],
    market_data: Any,
    counterparty_buckets: Mapping[str, Tuple[str, bool]],
    hedges: Sequence[Any] = (),
    reporting_currency: str = "USD",
    curve_currency: Optional[Mapping[str, str]] = None,
    reference_buckets: Optional[Mapping[str, int]] = None,
    equity_buckets: Optional[Mapping[str, int]] = None,
    commodity_buckets: Optional[Mapping[str, int]] = None,
    vol_buckets: Optional[Mapping[str, Tuple[str, Any]]] = None,
) -> List[CVASensitivity]:
    """
    Args:
        cva_fn: market data -> CVA (positive number)
        counterparty_buckets: counterparty credit-curve name -> (MAR50 bucket '1a'...'8', investment grade?)
        hedges: Eligible hedge products (their MV sensitivities enter with the sign flipped)
        reference_buckets: other credit-curve names -> RCS bucket 1-17 (default 15)
        equity_buckets / commodity_buckets: name -> bucket (defaults 11 / FRTB commodity map)
        vol_buckets: vol surface name -> (risk class 'IR'|'FX'|'RCS'|'EQ'|'CM', bucket); default from the name
    """
    ccy_of = {**INDEX_CURRENCY, **(curve_currency or {})}
    ref_b, eq_b = reference_buckets or {}, equity_buckets or {}
    cm_b = {**COMMODITY_BUCKET, **(commodity_buckets or {})}
    keys = enumerate_risk_factors(market_data)
    base_cva = cva_fn(market_data)

    def hedge_mv(md):
        return sum(fx_convert(md, float(r.npv), _currency_code(r.currency), reporting_currency)
                   for r in (h.price(md) for h in hedges))
    base_mv = hedge_mv(market_data) if hedges else 0.0

    def sens(shocks: List[Shock], scale: float) -> Tuple[float, float]:
        if not shocks:
            return 0.0, 0.0
        md = apply_shocks(market_data, shocks)
        s_cva = (cva_fn(md) - base_cva) / scale
        s_hdg = -(hedge_mv(md) - base_mv) / scale if hedges else 0.0
        return s_cva, s_hdg

    out: List[CVASensitivity] = []

    # ---- interest rate delta
    rate_keys: Dict[str, List[RiskFactorKey]] = {}
    for k in keys:
        if k.kind is FactorKind.RATE and k.field in ("discount_curve", "forward_curves"):
            ccy = reporting_currency if k.field == "discount_curve" else ccy_of.get(k.name, reporting_currency)
            rate_keys.setdefault(ccy, []).append(k)
    for ccy, ks in rate_keys.items():
        if ccy in IR_SPECIFIED or ccy == reporting_currency:
            for i, tenor in enumerate(IR_TENORS):
                w = _hat(IR_TENORS, i)
                s_c, s_h = sens([Shock(k, 1e-4 * w(k.tenor), ShockType.ABSOLUTE) for k in ks if w(k.tenor)], 1e-4)
                out.append(CVASensitivity("IR", "delta", ccy, tenor, s_c, s_h, IR_RW_SPECIFIED[tenor]))
        else:
            s_c, s_h = sens([Shock(k, 1e-4, ShockType.ABSOLUTE) for k in ks], 1e-4)
            out.append(CVASensitivity("IR", "delta", ccy, "parallel", s_c, s_h, IR_RW_OTHER))

    # ---- FX delta (each foreign currency up 1% against the reporting currency)
    currencies = set()
    for k in keys:
        if k.field == "fx_spots" and k.name and len(k.name) == 6:
            currencies.update({k.name[:3], k.name[3:]} - {reporting_currency})
    for ccy in sorted(currencies):
        shocks = []
        for k in keys:
            if k.field == "fx_spots" and k.name and len(k.name) == 6:
                if k.name[:3] == ccy:
                    shocks.append(Shock(k, 0.01, ShockType.RELATIVE))
                elif k.name[3:] == ccy:
                    shocks.append(Shock(k, 1 / 1.01 - 1, ShockType.RELATIVE))
        s_c, s_h = sens(shocks, 0.01)
        out.append(CVASensitivity("FX", "delta", ccy, ccy, s_c, s_h, FX_RW))

    # ---- counterparty credit spread delta
    credit = {}
    for k in keys:
        if k.field == "credit_curves":
            credit.setdefault(k.name, []).append(k)
    for name, (bucket, ig) in counterparty_buckets.items():
        ks = credit.get(name, [])
        for i, tenor in enumerate(CCS_TENORS):
            w = _hat(CCS_TENORS, i)
            s_c, s_h = sens([Shock(k, 1e-4 * w(k.tenor), ShockType.ABSOLUTE) for k in ks if w(k.tenor)], 1e-4)
            rw = CCS_RW[str(bucket)][0 if ig else 1]
            out.append(CVASensitivity("CCS", "delta", str(bucket), (name, tenor), s_c, s_h, rw, {"ig": ig}))

    # ---- reference credit spread delta (one factor per bucket)
    ref_groups: Dict[int, List[RiskFactorKey]] = {}
    for name, ks in credit.items():
        if name not in counterparty_buckets:
            ref_groups.setdefault(ref_b.get(name, 15), []).extend(ks)
    for b, ks in ref_groups.items():
        s_c, s_h = sens([Shock(k, 1e-4, ShockType.ABSOLUTE) for k in ks], 1e-4)
        out.append(CVASensitivity("RCS", "delta", b, None, s_c, s_h, RCS_RW[b]))

    # ---- equity / commodity delta (one factor per bucket)
    for field_name, cls, bucket_of, rw_table in (("equity_prices", "EQ", lambda n: eq_b.get(n, 11), EQ_RW),
                                                 ("commodity_prices", "CM", lambda n: cm_b.get(n.upper(), 11), CM_RW)):
        groups: Dict[int, List[RiskFactorKey]] = {}
        for k in keys:
            if k.field == field_name:
                groups.setdefault(bucket_of(k.name), []).append(k)
        for b, ks in groups.items():
            s_c, s_h = sens([Shock(k, 0.01, ShockType.RELATIVE) for k in ks], 0.01)
            out.append(CVASensitivity(cls, "delta", b, None, s_c, s_h, rw_table[b]))

    # ---- vega (one factor per bucket: all vols of the bucket +1% relative)
    vol_map = vol_buckets or {}
    vol_groups: Dict[Tuple[str, Any], List[RiskFactorKey]] = {}
    for k in keys:
        if k.kind is not FactorKind.VOLATILITY:
            continue
        if k.name in vol_map:
            cls, b = vol_map[k.name]
        else:
            rc = k.risk_class
            cls = {RiskClass.INTEREST_RATE: "IR", RiskClass.FX: "FX", RiskClass.CREDIT: "RCS",
                   RiskClass.EQUITY: "EQ", RiskClass.COMMODITY: "CM"}.get(rc)
            if cls is None:
                continue
            b = reporting_currency if cls in ("IR", "FX") else {"RCS": 15, "EQ": 11, "CM": 11}[cls]
        vol_groups.setdefault((cls, b), []).append(k)
    for (cls, b), ks in vol_groups.items():
        s_c, s_h = sens([Shock(k, 0.01, ShockType.RELATIVE) for k in ks], 0.01)
        rw = VEGA_RW_EQ_LARGE if cls == "EQ" and b in range(1, 9) else VEGA_RW_DEFAULT
        out.append(CVASensitivity(cls, "vega", b, None, s_c, s_h, rw))
    return out


# =============================================================================
# Aggregation
# =============================================================================

def _ccs_gamma_index(bucket: str) -> int:
    return 1 if bucket in ("1a", "1b") else int(bucket)


def _rho(a: CVASensitivity, b: CVASensitivity) -> float:
    if a.risk_class == "IR" and a.risk_type == "delta":
        if a.factor == b.factor:
            return 1.0
        if "parallel" in (a.factor, b.factor):
            return 1.0
        return IR_RHO[tuple(sorted((a.factor, b.factor)))]
    if a.risk_class == "CCS":
        (name_a, t_a), (name_b, t_b) = a.factor, b.factor
        tenor = 1.0 if t_a == t_b else 0.9
        if a.bucket == "8":
            name = 1.0 if name_a == name_b else 0.8
        else:
            name = 1.0 if name_a == name_b else 0.5
        quality = 1.0 if a.meta.get("ig") == b.meta.get("ig") else 0.8
        return tenor * name * quality
    return 1.0                                       # single factor per bucket


def _gamma(cls: str, b: Any, c: Any) -> float:
    if cls == "IR":
        return IR_GAMMA
    if cls == "FX":
        return FX_GAMMA
    if cls == "CCS":
        return _CCS_GAMMA_ROWS[_ccs_gamma_index(b)][_ccs_gamma_index(c) - 1]
    if cls == "RCS":
        if 15 in (b, c):
            return 0.0
        if {b, c} == {16, 17}:
            return 0.75
        if b in (16, 17) or c in (16, 17):
            return 0.45
        sb, sc = (b - 1) % 7 + 1, (c - 1) % 7 + 1
        g = 1.0 if sb == sc else _RCS_SECTOR_GAMMA[tuple(sorted((sb, sc)))]
        return g if (b <= 7) == (c <= 7) else g / 2
    if cls == "EQ":
        return eq_gamma(b, c)
    if cls == "CM":
        return 0.0 if 11 in (b, c) else 0.20
    raise ValueError(cls)


def sa_cva_aggregate(sensitivities: Sequence[CVASensitivity], m_cva: float = M_CVA) -> SACVAResult:
    groups: Dict[Tuple[str, str], Dict[Any, List[CVASensitivity]]] = {}
    for s in sensitivities:
        groups.setdefault((s.risk_class, s.risk_type), {}).setdefault(s.bucket, []).append(s)
    by_component, by_bucket = {}, {}
    for (cls, rtype), buckets in groups.items():
        kb, sb = {}, {}
        for b, xs in buckets.items():
            ws = np.array([x.ws for x in xs])
            corr = np.array([[1.0 if i == j else _rho(xs[i], xs[j]) for j in range(len(xs))] for i in range(len(xs))])
            hedge = sum((x.rw * x.s_hdg) ** 2 for x in xs)
            kb[b] = math.sqrt(max(float(ws @ corr @ ws) + R_HEDGE * hedge, 0.0))
            sb[b] = max(min(float(ws.sum()), kb[b]), -kb[b])
            by_bucket[(cls, rtype, b)] = kb[b]
        names = list(kb)
        total = sum(kb[b] ** 2 for b in names)
        for i, b in enumerate(names):
            for c in names[i + 1:]:
                total += 2 * _gamma(cls, b, c) * sb[b] * sb[c]
        by_component[(cls, rtype)] = m_cva * math.sqrt(max(total, 0.0))
    return SACVAResult(sum(by_component.values()), by_component, by_bucket, list(sensitivities))


def sa_cva_capital(cva_fn: Callable[[Any], float], market_data: Any,
                   counterparty_buckets: Mapping[str, Tuple[str, bool]], hedges: Sequence[Any] = (),
                   m_cva: float = M_CVA, **kwargs) -> SACVAResult:
    """Sensitivities + aggregation; kwargs are passed to sa_cva_sensitivities."""
    return sa_cva_aggregate(sa_cva_sensitivities(cva_fn, market_data, counterparty_buckets, hedges, **kwargs), m_cva)


__all__ = ["CVASensitivity", "SACVAResult", "cva_from_profile", "sa_cva_sensitivities", "sa_cva_aggregate",
           "sa_cva_capital"]
