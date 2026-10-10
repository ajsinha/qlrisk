"""
QLRisk - FRTB Internal Models Approach (MAR33)
==============================================

Liquidity-horizon ES (MAR33.4), with T = 10 days and LH_j in {10, 20, 40, 60, 120}:

    ES = sqrt( ES_T(P)^2 + sum_{j>=2} ( ES_T(P, j) * sqrt((LH_j - LH_{j-1}) / T) )^2 )

ES_T(P, j) is the 10-day 97.5% ES when only factors with LH >= LH_j move.

Stress calibration (MAR33.5): ES = ES_R,S x max(ES_F,C / ES_R,C, 1)
IMCC (MAR33.15): rho * ES_unconstrained + (1 - rho) * sum of per-risk-class ES, rho = 0.5
NMRF (MAR31.12 RFET; MAR33.16-17 SES aggregation, rho = 0.6)
Capital (MAR33.41): max(IMCC + SES, m_c * avg60(IMCC) + avg60(SES)) + DRC

Simplifications: the stress period is searched with Taylor P&L on the full factor set and
shared by all IMCC components; each NMRF's SES is the 97.5% ES of its own stressed 10-day
moves scaled by sqrt(LH / 10); IMA DRC uses a two-factor (global + sector) Gaussian copula.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Sequence

import numpy as np
from scipy.stats import norm

from ..calculator.python.pd_calculator import PDCalculator
from ..calculator.python.var_calculators import expected_shortfall
from ..riskfactors.taxonomy import FactorKind, RiskClass, RiskFactorKey
from ..riskfactors.timeseries import RiskFactorTimeSeries
from ..scenarios.generators import historical_scenarios
from ..scenarios.scenario_set import ScenarioSet
from ..scenarios.stressed_period import find_stress_window
from .frtb_sa.drc import DRCPosition
from .frtb_sa.parameters import COMMODITY_BUCKET, INDEX_CURRENCY

LH_BUCKETS = (10, 20, 40, 60, 120)
MAJOR_CCY = {"USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "SEK", "NZD", "NOK", "DKK", "HKD", "SGD", "MXN"}


def default_liquidity_horizon(key: RiskFactorKey, reporting_currency: str = "USD",
                              small_caps: Iterable[str] = (), high_yield: Iterable[str] = ()) -> int:
    """MAR33.12 liquidity horizons, mapped from the factor key."""
    rc, kind = key.risk_class, key.kind
    if kind is FactorKind.VOLATILITY:
        return {RiskClass.INTEREST_RATE: 60, RiskClass.CREDIT: 120, RiskClass.FX: 40,
                RiskClass.COMMODITY: 120}.get(rc, 60 if key.name in set(small_caps) else 20)
    if rc is RiskClass.INTEREST_RATE:
        ccy = reporting_currency if key.field == "discount_curve" else INDEX_CURRENCY.get(key.name or "", "")
        return 10 if ccy in MAJOR_CCY else 20
    if rc is RiskClass.CREDIT:
        return 60 if key.name in set(high_yield) else 40
    if rc is RiskClass.EQUITY:
        return 20 if key.name in set(small_caps) else 10
    if rc is RiskClass.FX:
        pair = key.name or ""
        return 10 if pair[:3] in MAJOR_CCY and pair[3:] in MAJOR_CCY else 20
    if rc is RiskClass.COMMODITY:
        return 20 if COMMODITY_BUCKET.get((key.name or "").upper(), 11) in (1, 2, 3, 5, 6, 7) else 60
    return 20


def _mask(scen: ScenarioSet, keep: Callable[[RiskFactorKey], bool]) -> ScenarioSet:
    r = scen.returns.copy()
    for j, k in enumerate(scen.factors):
        if not keep(k):
            r[:, j] = np.nan
    return ScenarioSet(scen.factors, r, scen.return_types, list(scen.labels), scen.weights, scen.horizon_days,
                       scen.method, dict(scen.metadata))


def liquidity_adjusted_es(pnl_fn: Callable[[ScenarioSet], np.ndarray], scenarios: ScenarioSet,
                          lh: Mapping[RiskFactorKey, int], confidence: float = 0.975) -> Dict[str, Any]:
    """
    MAR33.4 cascade. pnl_fn(scenario_set) returns portfolio P&L per scenario; `scenarios` are 10-day moves.
    Returns {'es', 'components': {LH_j: ES_T(P, j)}}.
    """
    comps, total, prev = {}, 0.0, None
    for lh_j in LH_BUCKETS:
        es_j = expected_shortfall(pnl_fn(_mask(scenarios, lambda k, l=lh_j: lh.get(k, 20) >= l)), confidence)
        comps[lh_j] = es_j
        total += es_j ** 2 if prev is None else (es_j * math.sqrt((lh_j - prev) / 10.0)) ** 2
        prev = lh_j
    return {"es": math.sqrt(total), "components": comps}


@dataclass
class IMCCResult:
    imcc: float
    es_unconstrained: float
    es_by_class: Dict[str, float]
    stress_window: tuple
    ratio: float
    details: Dict[str, Any] = field(default_factory=dict)


def imcc(
    engine: Any,
    trades: Sequence[Any],
    market_data: Any,
    history: RiskFactorTimeSeries,
    reduced_set: Optional[Iterable[RiskFactorKey]] = None,
    lh: Optional[Mapping[RiskFactorKey, int]] = None,
    current_window: int = 250,
    stress_window: int = 250,
    rho: float = 0.5,
    method: str = "taylor",
) -> IMCCResult:
    """
    Stress-calibrated, liquidity-adjusted IMCC for the portfolio, using a MarketRiskEngine for P&L.
    The reduced set defaults to all factors with history.
    """
    trades = list(trades)
    sens = engine.sensitivities(trades, market_data) if method == "taylor" else None
    tenday = historical_scenarios(history, horizon=10).restrict_to(market_data)
    lh = dict(lh or {k: default_liquidity_horizon(k, engine.reporting_currency or "USD") for k in tenday.factors})
    reduced = set(reduced_set) if reduced_set is not None else set(tenday.factors)
    pnl_fn = lambda s: engine.scenario_pnl(trades, market_data, s, method, sensitivities=sens).portfolio
    
    # stress window: maximise 10-day ES of the reduced set over history
    reduced_all = _mask(tenday, lambda k: k in reduced)
    win = find_stress_window(pnl_fn(reduced_all), tenday.labels, stress_window, 0.975, measure="es")
    stressed = tenday.subset(range(win.start_index, win.end_index))
    current = tenday.subset(range(len(tenday) - current_window, len(tenday)))
    
    def calibrated(keep: Callable[[RiskFactorKey], bool]) -> Dict[str, float]:
        es_rs = liquidity_adjusted_es(pnl_fn, _mask(stressed, lambda k: keep(k) and k in reduced), lh)["es"]
        es_fc = liquidity_adjusted_es(pnl_fn, _mask(current, keep), lh)["es"]
        es_rc = liquidity_adjusted_es(pnl_fn, _mask(current, lambda k: keep(k) and k in reduced), lh)["es"]
        ratio = max(es_fc / es_rc, 1.0) if es_rc > 0 else 1.0
        return {"es": es_rs * ratio, "ratio": ratio, "es_rs": es_rs, "es_fc": es_fc, "es_rc": es_rc}
    
    total = calibrated(lambda k: True)
    classes = sorted({k.risk_class for k in tenday.factors}, key=lambda c: c.value)
    by_class = {c.value: calibrated(lambda k, c=c: k.risk_class is c)["es"] for c in classes}
    value = rho * total["es"] + (1 - rho) * sum(by_class.values())
    return IMCCResult(value, total["es"], by_class, (win.start, win.end), total["ratio"], total)


def rfet(observations: Sequence[date], as_of: date) -> bool:
    """
    Risk factor eligibility test (MAR31.12): over the last 12 months, at least 24 real-price
    observations with no 90-day period containing fewer than 4, or at least 100 observations.
    """
    start = as_of - timedelta(days=365)
    obs = sorted(d for d in observations if start < d <= as_of)
    if len(obs) >= 100:
        return True
    if len(obs) < 24:
        return False
    day = start
    while day + timedelta(days=90) <= as_of:
        if sum(1 for d in obs if day < d <= day + timedelta(days=90)) < 4:
            return False
        day += timedelta(days=1)
    return True


def ses(
    engine: Any,
    trades: Sequence[Any],
    market_data: Any,
    history: RiskFactorTimeSeries,
    nmrf: Iterable[RiskFactorKey],
    stress_window: tuple,
    lh: Optional[Mapping[RiskFactorKey, int]] = None,
    idiosyncratic: Iterable[RiskFactorKey] = (),
    rho: float = 0.6,
) -> Dict[str, Any]:
    """Stressed expected shortfall for non-modellable factors, aggregated per MAR33.16-17."""
    trades = list(trades)
    tenday = historical_scenarios(history, horizon=10).restrict_to(market_data)
    rows = [i for i, d in enumerate(tenday.labels) if stress_window[0] <= d <= stress_window[1]]
    stressed = tenday.subset(rows)
    sens = engine.sensitivities(trades, market_data)
    idio = set(idiosyncratic)
    per_factor = {}
    for k in nmrf:
        if k not in tenday.factors:
            continue
        pnl = engine.scenario_pnl(trades, market_data, _mask(stressed, lambda f, k=k: f == k), "taylor",
                                  sensitivities=sens).portfolio
        horizon = (lh or {}).get(k, default_liquidity_horizon(k, engine.reporting_currency or "USD"))
        per_factor[k] = expected_shortfall(pnl, 0.975) * math.sqrt(max(horizon, 10) / 10.0)
    idio_vals = [v for k, v in per_factor.items() if k in idio]
    other = [v for k, v in per_factor.items() if k not in idio]
    total = math.sqrt(sum(v * v for v in idio_vals)) + math.sqrt((rho * sum(other)) ** 2 + (1 - rho ** 2) * sum(v * v for v in other))
    return {"ses": total, "by_factor": per_factor}


def ima_capital(imcc_value: float, ses_value: float, drc: float = 0.0, multiplier: float = 1.5,
                imcc_avg60: Optional[float] = None, ses_avg60: Optional[float] = None) -> float:
    """MAR33.41: max(IMCC + SES, m_c * avg(IMCC) + avg(SES)) + DRC; averages default to today's values."""
    a_imcc = imcc_value if imcc_avg60 is None else imcc_avg60
    a_ses = ses_value if ses_avg60 is None else ses_avg60
    return max(imcc_value + ses_value, multiplier * a_imcc + a_ses) + drc


def ima_drc(positions: Sequence[DRCPosition], n_sims: int = 200_000, global_correlation: float = 0.15,
            sector_correlation: float = 0.10, sectors: Optional[Mapping[str, str]] = None,
            confidence: float = 0.999, seed: Optional[int] = 0, pd_floor: float = 0.0003) -> Dict[str, float]:
    """
    1-year 99.9% default loss with two types of systematic factors (MAR33.26): a global factor and one
    factor per sector. Asset value of obligor i in sector s:
        A_i = sqrt(rho_g) G + sqrt(rho_s) S_s + sqrt(1 - rho_g - rho_s) e_i
    PD from the rating table (floored at 3bp); JTD from DRCPosition (not maturity-scaled; 1-year horizon).
    `sectors` maps obligor -> sector (default: the position's DRC bucket).
    """
    if global_correlation + sector_correlation >= 1:
        raise ValueError("global + sector correlation must be < 1")
    pds = PDCalculator.RATING_PDS
    pos = list(positions)
    sector_of = [(sectors or {}).get(p.obligor, p.bucket) for p in pos]
    names = sorted(set(sector_of))
    col = {s: i for i, s in enumerate(names)}
    thresholds = np.array([norm.ppf(max(pds.get(p.rating.upper(), 0.015), pd_floor)) for p in pos])
    jtd = np.array([p.jtd / min(max(p.maturity, 0.25), 1.0) for p in pos])
    rng = np.random.default_rng(seed)
    g = rng.standard_normal((n_sims, 1))
    s = rng.standard_normal((n_sims, len(names)))[:, [col[x] for x in sector_of]]
    eps = rng.standard_normal((n_sims, len(pos)))
    idio = math.sqrt(1 - global_correlation - sector_correlation)
    assets = math.sqrt(global_correlation) * g + math.sqrt(sector_correlation) * s + idio * eps
    losses = (assets < thresholds) @ jtd
    return {"drc": float(np.quantile(losses, confidence)), "expected_loss": float(losses.mean())}


__all__ = ["LH_BUCKETS", "default_liquidity_horizon", "liquidity_adjusted_es", "IMCCResult", "imcc",
           "rfet", "ses", "ima_capital", "ima_drc"]
