"""
QLRisk - Market Risk Result Models
==================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RiskMeasureResult:
    """
    A VaR or Expected Shortfall figure.
    
    Attributes:
        measure: 'VaR' or 'ES'
        value: Loss as a positive number (P&L convention: gains positive)
        confidence: e.g. 0.99
        horizon_days: Holding period the figure refers to
        method: e.g. 'historical', 'filtered_historical', 'parametric', 'monte_carlo', 'taylor'
        n_scenarios: Scenarios used
        currency: Reporting currency (None = trade currencies, single-currency books only)
        contributions: Component (Euler) contributions by trade or group; sum to value
        tail_scenarios: Labels of the scenarios that define the tail (worst first)
        metadata: Extra details (window, scaling, ...)
    """
    measure: str
    value: float
    confidence: float
    horizon_days: int = 1
    method: str = "historical"
    n_scenarios: int = 0
    currency: Optional[str] = None
    contributions: Dict[str, float] = field(default_factory=dict)
    tail_scenarios: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        ccy = f" {self.currency}" if self.currency else ""
        return (f"{self.measure}({self.confidence:.1%}, {self.horizon_days}d, {self.method}) = "
                f"{self.value:,.2f}{ccy} [{self.n_scenarios} scenarios]")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "measure": self.measure, "value": self.value, "confidence": self.confidence,
            "horizon_days": self.horizon_days, "method": self.method, "n_scenarios": self.n_scenarios,
            "currency": self.currency, "contributions": dict(self.contributions),
            "tail_scenarios": [str(s) for s in self.tail_scenarios], "metadata": dict(self.metadata),
        }


__all__ = ["RiskMeasureResult"]
