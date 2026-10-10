"""
QLRisk - Wrong-Way Risk
=======================

Exposure to a counterparty conditional on its credit deteriorating.

Every market factor's 1-day return is regressed on the counterparty's
credit-spread return (beta_j = cov(r_j, r_c) / var(r_c)). The conditional
scenario moves the spread by `shock_sigmas` standard deviations and every
other factor by beta_j times that move. The ratio of conditional to base
exposure measures wrong-way (> 1) or right-way (< 1) risk.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence

import numpy as np

from ..riskfactors.taxonomy import RiskFactorKey, RiskFactorLike, as_key
from ..riskfactors.timeseries import RiskFactorTimeSeries
from ..sensitivities.engine import _currency_code, fx_convert
from .generators import historical_scenarios
from .scenario_set import ScenarioSet


@dataclass
class WrongWayResult:
    base_exposure: float
    conditional_exposure: float
    ratio: float
    spread_move: float
    scenario: ScenarioSet = field(repr=False)
    top_moves: Dict[RiskFactorKey, float] = field(default_factory=dict)


def wrong_way_exposure(
    trades: Sequence[Any],
    market_data: Any,
    history: RiskFactorTimeSeries,
    credit_factor: RiskFactorLike,
    shock_sigmas: float = 3.0,
    horizon_days: int = 10,
    lookback: Optional[int] = None,
    reporting_currency: Optional[str] = None,
    top_n: int = 5,
) -> WrongWayResult:
    """
    Current exposure max(sum MtM, 0) of `trades` (one counterparty / netting set) today and under a
    `shock_sigmas`-sigma, `horizon_days` widening of the counterparty's credit spread with all
    other factors moved by their regression beta.
    """
    key = as_key(credit_factor)
    scen = historical_scenarios(history, lookback=lookback).restrict_to(market_data)
    if key not in scen.factors:
        raise KeyError(f"{key} has no history in the market data")
    r = np.nan_to_num(scen.returns, nan=0.0)
    c = scen.factors.index(key)
    var_c = r[:, c].var()
    if var_c <= 0:
        raise ValueError(f"{key} has no variation in its history")
    betas = ((r - r.mean(axis=0)) * (r[:, c] - r[:, c].mean())[:, None]).mean(axis=0) / var_c
    move = shock_sigmas * np.sqrt(var_c * horizon_days)
    row = betas * move
    row[c] = move
    conditional = ScenarioSet(scen.factors, row[None, :], scen.return_types, ["wrong_way"],
                              horizon_days=horizon_days, method="wrong_way")

    def exposure(md: Any) -> float:
        total = 0.0
        for t in trades:
            res = t.price(md)
            total += fx_convert(md, float(res.npv), _currency_code(res.currency), reporting_currency) \
                if reporting_currency else float(res.npv)
        return max(total, 0.0)

    base = exposure(market_data)
    stressed = exposure(conditional.market_data(0, market_data))
    order = np.argsort(-np.abs(row))[:top_n]
    return WrongWayResult(base, stressed, stressed / base if base > 0 else float("inf") if stressed > 0 else 1.0,
                          float(move), conditional, {scen.factors[i]: float(row[i]) for i in order})


__all__ = ["wrong_way_exposure", "WrongWayResult"]
