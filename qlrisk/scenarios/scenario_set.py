"""
QLRisk - Scenario Sets
======================

A scenario set is a matrix of risk-factor moves (scenarios x factors) with
the return convention of each factor. Moves are applied to today's market
data to build scenario market data (full revaluation) or multiplied by
sensitivities (Taylor P&L). NaN means "no move".

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from ..riskfactors.mapping import enumerate_risk_factors
from ..riskfactors.shocks import Shock, ShockType, apply_shocks
from ..riskfactors.taxonomy import RiskFactorKey, RiskFactorLike, as_key


@dataclass
class ScenarioSet:
    """
    Attributes:
        factors: Risk factors (columns)
        returns: (n_scenarios, n_factors) moves in each factor's return convention
        return_types: Convention per factor (ABSOLUTE / RELATIVE / LOG)
        labels: Scenario identifiers (e.g. end dates of historical windows)
        weights: Optional scenario probabilities (None = equal)
        horizon_days: Holding period the moves represent
        method: Generator name, for reporting
        metadata: Generator parameters
    """
    factors: List[RiskFactorKey]
    returns: np.ndarray
    return_types: List[ShockType]
    labels: List[Any] = field(default_factory=list)
    weights: Optional[np.ndarray] = None
    horizon_days: int = 1
    method: str = "custom"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.factors = [as_key(f) for f in self.factors]
        self.returns = np.atleast_2d(np.asarray(self.returns, dtype=float))
        n, m = self.returns.shape
        if m != len(self.factors) or len(self.return_types) != m:
            raise ValueError("returns columns, factors and return_types must align")
        if not self.labels:
            self.labels = list(range(n))
        if len(self.labels) != n:
            raise ValueError("labels must have one entry per scenario")
        if self.weights is not None:
            self.weights = np.asarray(self.weights, dtype=float)
            if self.weights.shape != (n,):
                raise ValueError("weights must have one entry per scenario")
    
    def __len__(self) -> int:
        return self.returns.shape[0]
    
    def __repr__(self) -> str:
        return (f"ScenarioSet({len(self)} scenarios x {len(self.factors)} factors, "
                f"{self.horizon_days}d, {self.method})")
    
    @classmethod
    def from_shocks(cls, scenarios: Dict[Any, Sequence[Shock]], method: str = "hypothetical") -> "ScenarioSet":
        """Build from named lists of Shock (e.g. a stress library). Factors missing in a scenario do not move."""
        keys: Dict[RiskFactorKey, ShockType] = {}
        for shocks in scenarios.values():
            for s in shocks:
                if keys.setdefault(s.factor, s.shock_type) is not s.shock_type:
                    raise ValueError(f"{s.factor} uses different shock types across scenarios")
        factors = list(keys)
        col = {k: i for i, k in enumerate(factors)}
        returns = np.full((len(scenarios), len(factors)), np.nan)
        for row, shocks in enumerate(scenarios.values()):
            for s in shocks:
                returns[row, col[s.factor]] = s.size if np.isnan(returns[row, col[s.factor]]) \
                    else returns[row, col[s.factor]] + s.size
        return cls(factors, returns, [keys[f] for f in factors], list(scenarios), method=method)
    
    def shocks(self, i: int) -> List[Shock]:
        """Scenario i as a list of shocks (NaN moves skipped)."""
        return [Shock(k, float(r), t) for k, r, t in zip(self.factors, self.returns[i], self.return_types)
                if not np.isnan(r)]
    
    def restrict_to(self, market_data: Any) -> "ScenarioSet":
        """Drop factors that do not exist in the market data (they cannot be applied)."""
        present = set(enumerate_risk_factors(market_data))
        cols = [i for i, f in enumerate(self.factors) if f in present]
        if len(cols) == len(self.factors):
            return self
        return self.select_factors([self.factors[i] for i in cols])
    
    def select_factors(self, factors: Sequence[RiskFactorLike]) -> "ScenarioSet":
        keys = [as_key(f) for f in factors]
        idx = {f: i for i, f in enumerate(self.factors)}
        cols = [idx[k] for k in keys]
        return ScenarioSet(keys, self.returns[:, cols], [self.return_types[i] for i in cols], list(self.labels),
                           self.weights, self.horizon_days, self.method, dict(self.metadata))
    
    def subset(self, rows: Sequence[int]) -> "ScenarioSet":
        rows = list(rows)
        w = None if self.weights is None else self.weights[rows]
        return ScenarioSet(self.factors, self.returns[rows], self.return_types, [self.labels[i] for i in rows],
                           w, self.horizon_days, self.method, dict(self.metadata))
    
    def market_data(self, i: int, base: Any) -> Any:
        """Base market data moved by scenario i (factors absent from base must be removed first: restrict_to)."""
        return apply_shocks(base, self.shocks(i))


__all__ = ["ScenarioSet"]
