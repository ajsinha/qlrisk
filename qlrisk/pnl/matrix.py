"""
QLRisk - P&L Matrix
===================

Scenario P&L per trade (trades x scenarios) with VaR / ES and their
decomposition. P&L convention: gains positive, losses negative; VaR and
ES are reported as positive losses.

Component contributions are Euler allocations that sum to the total:
  - ES:  -(1/alpha) * sum over tail scenarios of tail weight x trade P&L
  - VaR: -(trade P&L in the VaR scenario)
Incremental VaR/ES of a trade = total - total without that trade.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Union

import numpy as np

from ..calculator.python.var_calculators import expected_shortfall, tail_indices, value_at_risk
from ..models.risk_measure import RiskMeasureResult


@dataclass
class PnLMatrix:
    """
    Attributes:
        trade_ids: Row labels
        labels: Scenario labels (columns)
        values: (n_trades, n_scenarios) P&L
        weights: Scenario probabilities (None = equal)
        horizon_days: Holding period of the scenarios
        method: How the P&L was produced, e.g. 'historical/full_revaluation'
        currency: Reporting currency
        base_pv: Base PV per trade
        errors: (trade_id, scenario label, message) for failed revaluations (P&L set to 0)
    """
    trade_ids: List[str]
    labels: List[Any]
    values: np.ndarray
    weights: Optional[np.ndarray] = None
    horizon_days: int = 1
    method: str = ""
    currency: Optional[str] = None
    base_pv: Dict[str, float] = field(default_factory=dict)
    errors: List[tuple] = field(default_factory=list)
    
    def __post_init__(self):
        self.values = np.atleast_2d(np.asarray(self.values, dtype=float))
        if self.values.shape != (len(self.trade_ids), len(self.labels)):
            raise ValueError("values must be (n_trades, n_scenarios)")
    
    def __repr__(self) -> str:
        return f"PnLMatrix({len(self.trade_ids)} trades x {len(self.labels)} scenarios, {self.method})"
    
    @property
    def portfolio(self) -> np.ndarray:
        """Portfolio P&L per scenario."""
        return self.values.sum(axis=0)
    
    def row(self, trade_id: str) -> np.ndarray:
        return self.values[self.trade_ids.index(trade_id)]
    
    def _with(self, trade_ids, values) -> "PnLMatrix":
        return PnLMatrix(list(trade_ids), list(self.labels), values, self.weights, self.horizon_days,
                         self.method, self.currency, {t: self.base_pv.get(t, 0.0) for t in trade_ids}, [])
    
    def subset(self, trade_ids: Sequence[str]) -> "PnLMatrix":
        rows = [self.trade_ids.index(t) for t in trade_ids]
        return self._with(trade_ids, self.values[rows])
    
    def group(self, groups: Union[Mapping[str, str], Callable[[str], str]]) -> "PnLMatrix":
        """Aggregate rows into groups (e.g. desk, book, asset class); mapping or function trade_id -> group."""
        fn = groups if callable(groups) else (lambda t: groups.get(t, "UNASSIGNED"))
        names: Dict[str, List[int]] = {}
        for i, t in enumerate(self.trade_ids):
            names.setdefault(fn(t), []).append(i)
        return self._with(list(names), np.array([self.values[idx].sum(axis=0) for idx in names.values()]))
    
    def merge(self, other: "PnLMatrix") -> "PnLMatrix":
        if list(other.labels) != list(self.labels):
            raise ValueError("Cannot merge P&L on different scenarios")
        return PnLMatrix(self.trade_ids + other.trade_ids, self.labels, np.vstack([self.values, other.values]),
                         self.weights, self.horizon_days, self.method, self.currency,
                         {**self.base_pv, **other.base_pv}, self.errors + other.errors)
    
    # ------------------------------------------------------------ measures
    
    def _result(self, measure: str, value: float, confidence: float, contributions, tail) -> RiskMeasureResult:
        return RiskMeasureResult(measure, value, confidence, self.horizon_days, self.method, len(self.labels),
                                 self.currency, contributions, [self.labels[i] for i in tail])
    
    def var(self, confidence: float = 0.99) -> RiskMeasureResult:
        """Portfolio VaR with component contributions per row."""
        total = self.portfolio
        value = value_at_risk(total, confidence, self.weights)
        idx, _ = tail_indices(total, confidence, self.weights)
        var_scenario = idx[-1]
        contrib = {t: float(-self.values[i, var_scenario]) for i, t in enumerate(self.trade_ids)}
        return self._result("VaR", value, confidence, contrib, idx)
    
    def es(self, confidence: float = 0.975) -> RiskMeasureResult:
        """Portfolio Expected Shortfall with Euler contributions per row."""
        total = self.portfolio
        value = expected_shortfall(total, confidence, self.weights)
        idx, mass = tail_indices(total, confidence, self.weights)
        alpha = 1.0 - confidence
        contrib = {t: float(-(self.values[i, idx] @ mass) / alpha) for i, t in enumerate(self.trade_ids)}
        return self._result("ES", value, confidence, contrib, idx)
    
    def incremental(self, confidence: float = 0.99, measure: str = "var") -> Dict[str, float]:
        """Change in portfolio VaR/ES from removing each row (positive = row adds risk)."""
        fn = value_at_risk if measure == "var" else expected_shortfall
        total = self.portfolio
        base = fn(total, confidence, self.weights)
        return {t: base - fn(total - self.values[i], confidence, self.weights) for i, t in enumerate(self.trade_ids)}
    
    def standalone(self, confidence: float = 0.99, measure: str = "var") -> Dict[str, float]:
        """VaR/ES of each row on its own (their sum exceeds the portfolio figure: diversification)."""
        fn = value_at_risk if measure == "var" else expected_shortfall
        return {t: fn(self.values[i], confidence, self.weights) for i, t in enumerate(self.trade_ids)}


__all__ = ["PnLMatrix"]
