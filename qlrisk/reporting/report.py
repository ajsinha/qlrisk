"""
QLRisk - Risk Report
====================

One structure for every number a risk run produces: headline metrics,
per-node metrics for the reporting hierarchy, and the full result objects.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import csv
import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional


@dataclass
class RiskReport:
    """
    Attributes:
        as_of: Valuation date
        currency: Reporting currency
        metrics: Headline numbers, e.g. {"var.1d": ..., "frtb_sa.total": ...}
        by_node: {node: {metric: value}} for the reporting hierarchy ("ALL" = whole book)
        results: Full result objects by section (SensitivityResult, PnLMatrix, FRTBSAResult, ...)
        notes: Caveats collected during the run
    """
    as_of: date
    currency: Optional[str]
    metrics: Dict[str, float] = field(default_factory=dict)
    by_node: Dict[str, Dict[str, float]] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    
    def value(self, metric: str, node: str = "ALL") -> Optional[float]:
        """A metric for a node; 'ALL' falls back to the headline metrics."""
        if metric in self.by_node.get(node, {}):
            return self.by_node[node][metric]
        return self.metrics.get(metric) if node == "ALL" else None
    
    def rows(self) -> List[Dict[str, Any]]:
        """Flat rows: one per (node, metric), headline metrics under node 'ALL'."""
        rows = [{"node": "ALL", "metric": k, "value": v} for k, v in self.metrics.items()]
        for node, vals in self.by_node.items():
            rows.extend({"node": node, "metric": k, "value": v} for k, v in vals.items()
                        if not (node == "ALL" and k in self.metrics))
        return rows
    
    def to_dict(self) -> Dict[str, Any]:
        return {"as_of": self.as_of.isoformat(), "currency": self.currency, "metrics": dict(self.metrics),
                "by_node": {n: dict(v) for n, v in self.by_node.items()}, "notes": list(self.notes)}
    
    def to_json(self, path: Optional[str] = None, indent: int = 2) -> str:
        text = json.dumps(self.to_dict(), indent=indent, default=str)
        if path:
            with open(path, "w") as fh:
                fh.write(text)
        return text
    
    def to_csv(self, path: str) -> None:
        with open(path, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["node", "metric", "value"])
            writer.writeheader()
            writer.writerows(self.rows())
    
    def __str__(self) -> str:
        width = max((len(k) for k in self.metrics), default=10)
        lines = [f"Risk report {self.as_of} ({self.currency or 'trade ccy'})", "-" * (width + 20)]
        lines += [f"{k:<{width}}  {v:>16,.0f}" for k, v in self.metrics.items()]
        if self.notes:
            lines += ["", "Notes:"] + [f"  - {n}" for n in self.notes]
        return "\n".join(lines)


__all__ = ["RiskReport"]
