"""
QLRisk - Backtesting Module v2.0.1
==================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.

---

VaR backtesting (Kupiec, Christoffersen, Basel traffic light) and ES
backtesting (Acerbi-Szekely Z1 / Z2).
"""

from .var_backtest import (
    backtest_var, VaRBacktestResult, kupiec_pof, christoffersen_independence,
    traffic_light, basel_multiplier, BASEL_PLUS_FACTOR,
)
from .es_backtest import backtest_es, ESBacktestResult, Z2_GREEN, Z2_RED

__all__ = [
    "backtest_var", "VaRBacktestResult", "kupiec_pof", "christoffersen_independence",
    "traffic_light", "basel_multiplier", "BASEL_PLUS_FACTOR",
    "backtest_es", "ESBacktestResult", "Z2_GREEN", "Z2_RED",
]
