"""
QLRisk - FRTB SA Residual Risk Add-On (MAR23)
=============================================

RRAO = sum(notional x 1.0%) for exotic underlyings + sum(notional x 0.1%) for other residual risks
(path-dependent / discontinuous payoffs, e.g. barriers and digitals, variance products).

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Any, Dict, Iterable, Sequence

from . import parameters as p

DEFAULT_OTHER_RESIDUAL = {"FXBarrierOption", "FXDigitalOption", "VarianceSwap"}


def rrao_charge(
    trades: Sequence[Any],
    exotic: Iterable[str] = (),
    other_residual: Iterable[str] = (),
    other_residual_types: Iterable[str] = DEFAULT_OTHER_RESIDUAL,
) -> Dict[str, Any]:
    """
    Args:
        trades: Trades (gross notional is used)
        exotic: trade_ids with exotic underlyings (1.0%)
        other_residual: trade_ids with other residual risk (0.1%)
        other_residual_types: product class names classified as other residual risk by default
    """
    exotic, other, types = set(exotic), set(other_residual), set(other_residual_types)
    by_trade = {}
    for t in trades:
        if t.trade_id in exotic:
            by_trade[t.trade_id] = abs(t.notional) * p.RRAO_EXOTIC
        elif t.trade_id in other or type(t).__name__ in types:
            by_trade[t.trade_id] = abs(t.notional) * p.RRAO_OTHER
    return {"total": sum(by_trade.values()), "by_trade": by_trade}


__all__ = ["rrao_charge", "DEFAULT_OTHER_RESIDUAL"]
