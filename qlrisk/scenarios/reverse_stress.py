"""
QLRisk - Reverse Stress Testing
===============================

Find the most plausible market move that produces a given loss.

Under the linear (delta) approximation P&L = e'r with return covariance C, the
move with the smallest Mahalanobis distance r'C^-1 r that loses L is

    r* = -L C e / (e' C e),        distance d = L / sqrt(e' C e)   (in 1-day sigmas)

The direction is then scaled by full revaluation until the actual loss is L.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from scipy.optimize import brentq

from ..riskfactors.mapping import get_factor_value
from ..riskfactors.shocks import Shock, ShockType
from ..riskfactors.taxonomy import RiskFactorKey
from ..riskfactors.timeseries import RiskFactorTimeSeries
from ..sensitivities.engine import SensitivityEngine, _currency_code, fx_convert
from .generators import covariance, historical_scenarios
from .scenario_set import ScenarioSet


@dataclass
class ReverseStressResult:
    target_loss: float
    achieved_loss: float
    scale: float                       # multiple of the linear solution needed under full revaluation
    sigma_distance: float              # Mahalanobis distance of the final move, in 1-day sigmas
    shocks: List[Shock]
    top_moves: Dict[RiskFactorKey, float] = field(default_factory=dict)   # largest moves in own-sigma units
    
    def scenario(self) -> ScenarioSet:
        return ScenarioSet.from_shocks({"reverse_stress": self.shocks}, method="reverse_stress")


def reverse_stress_test(
    trades: Sequence[Any],
    market_data: Any,
    history: RiskFactorTimeSeries,
    loss: float,
    lookback: Optional[int] = 250,
    reporting_currency: Optional[str] = None,
    max_scale: float = 20.0,
    top_n: int = 10,
) -> ReverseStressResult:
    """Most plausible scenario (minimum Mahalanobis distance) that loses `loss` (a positive number)."""
    if loss <= 0:
        raise ValueError("loss must be positive")
    trades = list(trades)
    scen = historical_scenarios(history, lookback=lookback).restrict_to(market_data)
    cov = covariance(scen.returns)
    sens = SensitivityEngine().compute(trades, market_data, reporting_currency=reporting_currency)
    col = {k: j for j, k in enumerate(scen.factors)}
    e = np.zeros(len(scen.factors))
    for rec in sens.records:
        if rec.factor in col and rec.derivative is not None:
            j = col[rec.factor]
            scale = 1.0 if scen.return_types[j] is ShockType.ABSOLUTE else get_factor_value(market_data, rec.factor)
            e[j] += rec.derivative * scale
    var_p = float(e @ cov @ e)
    if var_p <= 0:
        raise ValueError("portfolio has no exposure to factors with history")
    direction = -loss * (cov @ e) / var_p
    
    def shocks_for(k: float) -> List[Shock]:
        return [Shock(f, float(k * r), t) for f, r, t in zip(scen.factors, direction, scen.return_types) if r != 0.0]
    
    def pv(md: Any) -> float:
        total = 0.0
        for t in trades:
            res = t.price(md)
            total += fx_convert(md, float(res.npv), _currency_code(res.currency), reporting_currency) \
                if reporting_currency else float(res.npv)
        return total
    
    from ..riskfactors.shocks import apply_shocks
    base = pv(market_data)
    shortfall = lambda k: (base - pv(apply_shocks(market_data, shocks_for(k)))) - loss
    try:
        k = brentq(shortfall, 1e-6, max_scale, xtol=1e-6) if shortfall(max_scale) > 0 else max_scale
    except ValueError:
        k = 1.0
    achieved = shortfall(k) + loss
    sig = np.sqrt(np.clip(np.diag(cov), 1e-30, None))
    z = k * direction / sig
    order = np.argsort(-np.abs(z))[:top_n]
    return ReverseStressResult(loss, achieved, k, k * loss / np.sqrt(var_p), shocks_for(k),
                               {scen.factors[i]: float(z[i]) for i in order})


__all__ = ["reverse_stress_test", "ReverseStressResult"]
