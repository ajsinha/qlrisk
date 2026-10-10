"""
QLRisk - Liquidity-Adjusted VaR
===============================

Exogenous liquidity cost (Bangia et al.): closing a position costs half the
proportional bid-ask spread.

    LVaR = VaR + sum_i 0.5 * |position value_i| * spread_i
    VaR_LH = VaR_1d * sqrt(liquidity horizon in days)

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Mapping

import numpy as np


def liquidity_cost(position_values: Mapping[str, float], spreads: Mapping[str, float]) -> float:
    """Half-spread cost of liquidating every position (spreads are proportional, e.g. 0.002 = 20bp)."""
    return float(sum(0.5 * abs(v) * spreads.get(k, 0.0) for k, v in position_values.items()))


def liquidity_adjusted_var(var: float, position_values: Mapping[str, float], spreads: Mapping[str, float],
                           liquidity_horizon_days: int = 1) -> float:
    """VaR scaled to the liquidity horizon plus the exogenous liquidation cost."""
    return float(var * np.sqrt(liquidity_horizon_days) + liquidity_cost(position_values, spreads))


__all__ = ["liquidity_cost", "liquidity_adjusted_var"]
