"""
QLRisk - Sensitivity-Based (Taylor) P&L
=======================================

    P&L_trade(s) = sum_i delta_i * dx_i(s) + 1/2 * sum_i gamma_i * dx_i(s)^2

delta_i, gamma_i are natural-unit derivatives from a SensitivityResult
(diagonal gamma, central differences); dx_i is the factor move implied by
the scenario return (absolute: r; relative: x*r; log: x*(e^r - 1)).
Orders of magnitude faster than full revaluation; use it for large
scenario sets, stressed-window searches, and as a P&L-explain baseline.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Any

import numpy as np

from ..riskfactors.mapping import get_factor_value
from ..riskfactors.shocks import ShockType
from ..scenarios.scenario_set import ScenarioSet
from ..sensitivities.results import SensitivityResult
from .matrix import PnLMatrix


def factor_moves(scenarios: ScenarioSet, market_data: Any) -> np.ndarray:
    """Absolute factor moves dx (scenarios x factors) implied by the scenario returns at today's levels."""
    r = np.nan_to_num(scenarios.returns, nan=0.0)
    dx = np.empty_like(r)
    for j, (key, rt) in enumerate(zip(scenarios.factors, scenarios.return_types)):
        if rt is ShockType.ABSOLUTE:
            dx[:, j] = r[:, j]
        else:
            level = get_factor_value(market_data, key)
            dx[:, j] = level * (r[:, j] if rt is ShockType.RELATIVE else np.expm1(r[:, j]))
    return dx


def taylor_pnl(
    sensitivities: SensitivityResult,
    market_data: Any,
    scenarios: ScenarioSet,
    order: int = 2,
) -> PnLMatrix:
    """
    Delta (order=1) or delta-gamma (order=2) P&L for every trade in `sensitivities`.
    Sensitivities to factors that are not in the scenario set contribute nothing.
    """
    scen = scenarios.restrict_to(market_data)
    col = {k: j for j, k in enumerate(scen.factors)}
    dx = factor_moves(scen, market_data)
    trade_ids = list(sensitivities.base_pv)
    row = {t: i for i, t in enumerate(trade_ids)}
    values = np.zeros((len(trade_ids), len(scen)))
    for rec in sensitivities.records:
        if rec.factor not in col or rec.derivative is None or rec.trade_id not in row:
            continue
        move = dx[:, col[rec.factor]]
        pnl = rec.derivative * move
        if order >= 2 and rec.gamma is not None:
            level = get_factor_value(market_data, rec.factor)
            step = rec.bump_size * level if rec.bump_type is ShockType.RELATIVE else rec.bump_size
            pnl = pnl + 0.5 * (rec.gamma / step ** 2) * move ** 2
        values[row[rec.trade_id]] += pnl
    method = f"{scen.method}/{'delta' if order == 1 else 'delta_gamma'}"
    return PnLMatrix(trade_ids, list(scen.labels), values, scen.weights, scen.horizon_days, method,
                     sensitivities.currency, dict(sensitivities.base_pv))


__all__ = ["taylor_pnl", "factor_moves"]
