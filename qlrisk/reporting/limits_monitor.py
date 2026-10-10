"""
QLRisk - Limit Monitoring
=========================

    limits = [RiskLimit("Firm VaR", "var.1d", 2_000_000),
              RiskLimit("Rates DV01", "dv01.IR", 50_000, node="BankCo/Rates")]
    for check in check_limits(report, limits):
        print(check.name, check.utilisation, check.status)

Status thresholds reuse qlrisk.models.limit.LimitStatus: GREEN < 75%, AMBER < 90%,
RED <= 100%, BREACH > 100% (configurable per limit).

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass
from typing import List, Optional, Sequence

from ..models.limit import LimitStatus
from .report import RiskReport


@dataclass
class RiskLimit:
    """A limit on one report metric for one hierarchy node (absolute value compared unless absolute=False)."""
    name: str
    metric: str
    limit: float
    node: str = "ALL"
    amber: float = 0.75
    red: float = 0.90
    absolute: bool = True


@dataclass
class LimitCheck:
    name: str
    node: str
    metric: str
    value: Optional[float]
    limit: float
    utilisation: Optional[float]
    status: Optional[LimitStatus]
    
    def __str__(self) -> str:
        if self.value is None:
            return f"{self.name}: metric {self.metric} not available for {self.node}"
        return (f"{self.name:24} {self.node:22} {self.value:>14,.0f} / {self.limit:>14,.0f} "
                f"= {self.utilisation:6.1%}  {self.status.value.upper()}")


def check_limits(report: RiskReport, limits: Sequence[RiskLimit]) -> List[LimitCheck]:
    out = []
    for lim in limits:
        value = report.value(lim.metric, lim.node)
        if value is None:
            out.append(LimitCheck(lim.name, lim.node, lim.metric, None, lim.limit, None, None))
            continue
        used = (abs(value) if lim.absolute else value) / lim.limit
        status = (LimitStatus.BREACH if used > 1.0 else LimitStatus.RED if used >= lim.red
                  else LimitStatus.AMBER if used >= lim.amber else LimitStatus.GREEN)
        out.append(LimitCheck(lim.name, lim.node, lim.metric, value, lim.limit, used, status))
    return out


def breaches(checks: Sequence[LimitCheck]) -> List[LimitCheck]:
    return [c for c in checks if c.status is LimitStatus.BREACH]


__all__ = ["RiskLimit", "LimitCheck", "check_limits", "breaches"]
