"""
QLRisk - Market Data Shocks
===========================

Shock specifications and their application to market data. Shocking
always returns a copy-on-write clone; the input market data is never
mutated, so one base snapshot can be shared by many threads.

    from qlrisk.riskfactors import apply_shocks, curve_shocks, parallel, twist, ShockType

    up_1bp   = apply_shocks(md, {"IR.DISCOUNT.5Y": 0.0001})
    eq_down  = apply_shocks(md, {"EQ.AAPL": -0.10}, ShockType.RELATIVE)
    steepen  = apply_shocks(md, curve_shocks(md, "forward_curves", "SOFR", twist(-0.0010, 0.0010)))

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Iterable, List, Mapping, Optional, Union

from .mapping import clone_market_data, enumerate_risk_factors, get_factor_value, set_factor_value
from .taxonomy import RiskClass, RiskFactorKey, RiskFactorLike, as_key


class ShockType(Enum):
    """How a shock size combines with the base value."""
    ABSOLUTE = "absolute"   # v + s            (rates, spreads: s in decimal, 1bp = 0.0001)
    RELATIVE = "relative"   # v * (1 + s)      (prices, spots: s = 0.01 is +1%)
    LOG = "log"             # v * exp(s)       (log-return scenarios)


def shocked_value(base: float, size: float, shock_type: ShockType) -> float:
    """Apply one shock to one value."""
    if shock_type is ShockType.ABSOLUTE:
        return base + size
    if shock_type is ShockType.RELATIVE:
        return base * (1.0 + size)
    if shock_type is ShockType.LOG:
        return base * math.exp(size)
    raise ValueError(f"Unknown shock type: {shock_type}")


@dataclass(frozen=True)
class Shock:
    """A shock to one risk factor."""
    factor: RiskFactorKey
    size: float
    shock_type: ShockType = ShockType.ABSOLUTE

    def __post_init__(self):
        object.__setattr__(self, "factor", as_key(self.factor))


ShockInput = Union[Iterable[Shock], Mapping[RiskFactorLike, float]]


def _as_shocks(shocks: ShockInput, shock_type: ShockType) -> List[Shock]:
    if isinstance(shocks, Mapping):
        return [Shock(as_key(k), float(v), shock_type) for k, v in shocks.items()]
    return list(shocks)


def apply_shocks(
    market_data: Any,
    shocks: ShockInput,
    shock_type: ShockType = ShockType.ABSOLUTE,
) -> Any:
    """
    Return a shocked copy of the market data.

    Args:
        market_data: Base products.base.MarketData (not modified)
        shocks: Iterable of Shock, or mapping of factor -> size
        shock_type: Shock type for mapping input (ignored for Shock objects)

    Returns:
        New MarketData with only the touched fields copied
    """
    shock_list = _as_shocks(shocks, shock_type)
    if not shock_list:
        return market_data
    shocked = clone_market_data(market_data, {s.factor.field for s in shock_list})
    for s in shock_list:
        base = get_factor_value(shocked, s.factor)
        set_factor_value(shocked, s.factor, shocked_value(base, s.size, s.shock_type))
    return shocked


def set_factors(market_data: Any, values: Mapping[RiskFactorLike, float]) -> Any:
    """Return a copy of the market data with factors set to absolute levels."""
    keys = {as_key(k): float(v) for k, v in values.items()}
    updated = clone_market_data(market_data, {k.field for k in keys})
    for key, value in keys.items():
        set_factor_value(updated, key, value)
    return updated


# =============================================================================
# Curve shapes: functions tenor (years) -> shock size
# =============================================================================

CurveShape = Callable[[float], float]


def parallel(size: float) -> CurveShape:
    """Same shift at every tenor."""
    return lambda tenor: size


def twist(short_end: float, long_end: float, short_tenor: float = 2.0, long_tenor: float = 10.0) -> CurveShape:
    """Linear move from `short_end` (at/below short_tenor) to `long_end` (at/above long_tenor)."""
    def shape(tenor: float) -> float:
        if tenor <= short_tenor:
            return short_end
        if tenor >= long_tenor:
            return long_end
        w = (tenor - short_tenor) / (long_tenor - short_tenor)
        return short_end + w * (long_end - short_end)
    return shape


def butterfly(
    wings: float,
    belly: float,
    short_tenor: float = 2.0,
    belly_tenor: float = 5.0,
    long_tenor: float = 10.0,
) -> CurveShape:
    """`wings` at both ends, `belly` at belly_tenor, linear in between."""
    left, right = twist(wings, belly, short_tenor, belly_tenor), twist(belly, wings, belly_tenor, long_tenor)
    return lambda tenor: left(tenor) if tenor <= belly_tenor else right(tenor)


def curve_shocks(
    market_data: Any,
    field: Optional[str] = None,
    name: Optional[str] = None,
    shape: CurveShape = parallel(0.0001),
    shock_type: ShockType = ShockType.ABSOLUTE,
    risk_classes: Optional[Iterable[RiskClass]] = None,
) -> List[Shock]:
    """
    Shocks that move whole curves by a tenor-dependent shape.

    Args:
        market_data: Market data whose curve pillars are shocked
        field: MarketData field (e.g. 'discount_curve'); None = all fields
        name: Curve name within the field (e.g. 'SOFR'); None = all curves
        shape: Tenor -> size function (parallel, twist, butterfly, or custom)
        shock_type: How sizes apply
        risk_classes: Optional risk-class filter

    Returns:
        One Shock per matching tenored factor
    """
    keys = enumerate_risk_factors(
        market_data,
        risk_classes=risk_classes,
        fields=None if field is None else [field],
    )
    return [
        Shock(k, shape(k.tenor), shock_type)
        for k in keys
        if k.tenor is not None and (name is None or k.name == name)
    ]


__all__ = [
    "ShockType", "Shock", "shocked_value", "apply_shocks", "set_factors",
    "CurveShape", "parallel", "twist", "butterfly", "curve_shocks",
]
