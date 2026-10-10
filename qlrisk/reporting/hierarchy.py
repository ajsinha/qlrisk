"""
QLRisk - Reporting Hierarchy
============================

Organisation tree (e.g. legal entity / desk / book) over trades. Additive
measures (PV, sensitivities, stress P&L) are summed up the tree; VaR and ES
are NOT additive and are recomputed on each node's combined P&L vector.

    h = Hierarchy({"IRS-1": ("BankCo", "Rates", "USD Swaps"), "BOND-1": ("BankCo", "Credit", "IG")})
    h.var_by_node(pnl_matrix)          # {"ALL": ..., "BankCo": ..., "BankCo/Rates": ..., ...}

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..models.risk_measure import RiskMeasureResult
from ..pnl.matrix import PnLMatrix

ROOT = "ALL"


class Hierarchy:
    """
    Args:
        paths: trade_id -> path tuple, e.g. ("BankCo", "Rates", "USD Swaps")
        levels: Names of the path levels (for reporting only)
    Trades not in `paths` sit directly under the root.
    """
    
    def __init__(self, paths: Mapping[str, Sequence[str]], levels: Sequence[str] = ("entity", "desk", "book")):
        self.paths: Dict[str, Tuple[str, ...]] = {t: tuple(p) for t, p in paths.items()}
        self.levels = tuple(levels)
    
    @staticmethod
    def label(path: Sequence[str]) -> str:
        return "/".join(path) if path else ROOT
    
    def path_of(self, trade_id: str) -> Tuple[str, ...]:
        return self.paths.get(trade_id, ())
    
    def nodes(self, trade_ids: Optional[Sequence[str]] = None) -> List[str]:
        """Every node label (root first, then depth-first order of appearance)."""
        ids = trade_ids if trade_ids is not None else list(self.paths)
        seen: Dict[str, None] = {ROOT: None}
        for t in ids:
            p = self.path_of(t)
            for i in range(1, len(p) + 1):
                seen.setdefault(self.label(p[:i]), None)
        return list(seen)
    
    def trades_under(self, node: str, trade_ids: Sequence[str]) -> List[str]:
        if node == ROOT:
            return list(trade_ids)
        prefix = tuple(node.split("/"))
        return [t for t in trade_ids if self.path_of(t)[:len(prefix)] == prefix]
    
    def sum_by_node(self, values: Mapping[str, float]) -> Dict[str, float]:
        """Additive roll-up of per-trade values."""
        ids = list(values)
        return {n: sum(values[t] for t in self.trades_under(n, ids)) for n in self.nodes(ids)}
    
    def measure_by_node(self, pnl: PnLMatrix, confidence: float = 0.99, measure: str = "var") -> Dict[str, RiskMeasureResult]:
        """VaR / ES recomputed on each node's combined scenario P&L (non-additive)."""
        out = {}
        for n in self.nodes(pnl.trade_ids):
            ids = self.trades_under(n, pnl.trade_ids)
            if ids:
                sub = pnl.subset(ids)
                out[n] = sub.var(confidence) if measure == "var" else sub.es(confidence)
        return out
    
    def var_by_node(self, pnl: PnLMatrix, confidence: float = 0.99) -> Dict[str, RiskMeasureResult]:
        return self.measure_by_node(pnl, confidence, "var")
    
    def diversification(self, pnl: PnLMatrix, confidence: float = 0.99, measure: str = "var") -> Dict[str, float]:
        """Per node: sum of children's VaR/ES minus the node's own (>= 0 for diversified books)."""
        by_node = self.measure_by_node(pnl, confidence, measure)
        out = {}
        for n, res in by_node.items():
            depth = 0 if n == ROOT else len(n.split("/"))
            children = [c for c in by_node if c != ROOT and len(c.split("/")) == depth + 1
                        and (n == ROOT or c.startswith(n + "/"))]
            if children:
                out[n] = sum(by_node[c].value for c in children) - res.value
        return out


__all__ = ["Hierarchy", "ROOT"]
