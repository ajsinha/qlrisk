"""
QLRisk - Full Revaluation
=========================

Reprice every trade under every scenario: P&L = PV(scenario) - PV(base).

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional, Sequence

import numpy as np

from ..scenarios.scenario_set import ScenarioSet
from ..sensitivities.engine import _currency_code, fx_convert
from .matrix import PnLMatrix


def _pv(trade: Any, md: Any, ccy: Optional[str]) -> float:
    res = trade.price(md)
    return fx_convert(md, float(res.npv), _currency_code(res.currency), ccy) if ccy else float(res.npv)


def full_revaluation(
    trades: Sequence[Any],
    market_data: Any,
    scenarios: ScenarioSet,
    reporting_currency: Optional[str] = None,
    max_workers: int = 1,
) -> PnLMatrix:
    """
    Full-revaluation P&L for every trade under every scenario.
    
    Scenario factors absent from the market data are ignored. A trade that fails to
    price in a scenario gets 0 P&L there and an entry in `errors`.
    """
    trades = list(trades)
    ids = [t.trade_id for t in trades]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate trade_id in trades")
    scen = scenarios.restrict_to(market_data)
    base = {t.trade_id: _pv(t, market_data, reporting_currency) for t in trades}
    errors = []
    
    def column(j: int) -> np.ndarray:
        md = scen.market_data(j, market_data)
        out = np.zeros(len(trades))
        for i, t in enumerate(trades):
            try:
                out[i] = _pv(t, md, reporting_currency) - base[t.trade_id]
            except Exception as exc:
                errors.append((t.trade_id, scen.labels[j], f"{type(exc).__name__}: {exc}"))
        return out
    
    n = len(scen)
    if max_workers > 1 and n > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            cols = list(pool.map(column, range(n)))
    else:
        cols = [column(j) for j in range(n)]
    values = np.column_stack(cols) if cols else np.zeros((len(trades), 0))
    return PnLMatrix(ids, list(scen.labels), values, scen.weights, scen.horizon_days,
                     f"{scen.method}/full_revaluation", reporting_currency, base, errors)


__all__ = ["full_revaluation"]
