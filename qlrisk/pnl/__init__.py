"""
QLRisk - P&L Module v2.3.0
==========================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.

---

Scenario P&L: full revaluation and Taylor (sensitivity-based) P&L, in a
PnLMatrix that computes VaR / ES and their decomposition.
"""

from .matrix import PnLMatrix
from .revaluation import full_revaluation
from .taylor import taylor_pnl, factor_moves
from .attribution import explain_pnl, PnLExplain, TradeExplain, pla_test, PLAResult

__all__ = ["PnLMatrix", "full_revaluation", "taylor_pnl", "factor_moves",
           "explain_pnl", "PnLExplain", "TradeExplain", "pla_test", "PLAResult"]
