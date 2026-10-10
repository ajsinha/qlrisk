"""
QLRisk - Sensitivity Measures and Bump Conventions
==================================================

Conventions (PV change for an UP move of one bump unit):

    Factor kind     Bump                    First-order measure
    -----------     ----------------------  ----------------------------------
    RATE            +1bp absolute           DV01   (PV change per +1bp)
    SPREAD          +1bp absolute           CS01   (PV change per +1bp)
    DIVIDEND        +1bp absolute           DIV01  (PV change per +1bp)
    SPOT / PRICE    +1% relative            DELTA  (PV change per +1% move; "cash delta / 100")
    VOLATILITY      +1 vol point absolute   VEGA   (PV change per +1 vol point)
    SCALAR          +1bp absolute           DELTA

Each record also carries the derivative in natural units (dPV/dx) and,
with central differences, the second-order change (gamma per bump unit^2).

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from ..riskfactors.shocks import ShockType
from ..riskfactors.taxonomy import FactorKind, RiskClass, RiskFactorKey


class SensitivityMeasure(Enum):
    """Kind of sensitivity a record holds."""
    DV01 = "dv01"
    CS01 = "cs01"
    DIV01 = "div01"
    DELTA = "delta"
    VEGA = "vega"
    CROSS_GAMMA = "cross_gamma"
    THETA = "theta"


@dataclass(frozen=True)
class BumpSpec:
    """Bump size and type for one factor kind."""
    size: float
    shock_type: ShockType
    unit: str

    def bump_in_factor_units(self, level: float) -> float:
        """Size of the bump measured in the factor's own units."""
        return self.size * level if self.shock_type is ShockType.RELATIVE else self.size


DEFAULT_BUMPS: Dict[FactorKind, BumpSpec] = {
    FactorKind.RATE: BumpSpec(0.0001, ShockType.ABSOLUTE, "1bp"),
    FactorKind.SPREAD: BumpSpec(0.0001, ShockType.ABSOLUTE, "1bp"),
    FactorKind.DIVIDEND: BumpSpec(0.0001, ShockType.ABSOLUTE, "1bp"),
    FactorKind.SPOT: BumpSpec(0.01, ShockType.RELATIVE, "1%"),
    FactorKind.PRICE: BumpSpec(0.01, ShockType.RELATIVE, "1%"),
    FactorKind.VOLATILITY: BumpSpec(0.01, ShockType.ABSOLUTE, "1 vol pt"),
    FactorKind.SCALAR: BumpSpec(0.0001, ShockType.ABSOLUTE, "1bp"),
}

_MEASURE_BY_KIND = {
    FactorKind.RATE: SensitivityMeasure.DV01,
    FactorKind.SPREAD: SensitivityMeasure.CS01,
    FactorKind.DIVIDEND: SensitivityMeasure.DIV01,
    FactorKind.SPOT: SensitivityMeasure.DELTA,
    FactorKind.PRICE: SensitivityMeasure.DELTA,
    FactorKind.VOLATILITY: SensitivityMeasure.VEGA,
    FactorKind.SCALAR: SensitivityMeasure.DELTA,
}


def measure_for(factor: RiskFactorKey) -> SensitivityMeasure:
    """First-order measure name for a factor (DV01 for rates, VEGA for vols, ...)."""
    return _MEASURE_BY_KIND[factor.kind]


@dataclass(frozen=True)
class Sensitivity:
    """
    One sensitivity of one trade.

    Attributes:
        trade_id: Trade the sensitivity belongs to
        factor: Risk factor bumped (None for THETA)
        measure: DV01 / CS01 / DELTA / VEGA / ... / THETA / CROSS_GAMMA
        value: PV change per bump unit (see module conventions); for THETA the 1-day PV change;
               for CROSS_GAMMA the mixed second difference per (bump_i x bump_j)
        gamma: Second-order PV change per bump unit^2 (central differences only)
        derivative: dPV/dx in the factor's natural units
        bump_size: Bump size used
        bump_type: How the bump was applied
        currency: Currency of value / gamma / derivative
        factor2: Second factor for CROSS_GAMMA
    """
    trade_id: str
    factor: Optional[RiskFactorKey]
    measure: SensitivityMeasure
    value: float
    gamma: Optional[float] = None
    derivative: Optional[float] = None
    bump_size: Optional[float] = None
    bump_type: Optional[ShockType] = None
    currency: Optional[str] = None
    factor2: Optional[RiskFactorKey] = None

    @property
    def risk_class(self) -> Optional[RiskClass]:
        return self.factor.risk_class if self.factor is not None else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "factor": str(self.factor) if self.factor is not None else None,
            "factor2": str(self.factor2) if self.factor2 is not None else None,
            "risk_class": self.risk_class.value if self.risk_class else None,
            "measure": self.measure.value,
            "value": self.value,
            "gamma": self.gamma,
            "derivative": self.derivative,
            "bump_size": self.bump_size,
            "bump_type": self.bump_type.value if self.bump_type else None,
            "currency": self.currency,
        }


__all__ = [
    "SensitivityMeasure", "BumpSpec", "DEFAULT_BUMPS", "measure_for", "Sensitivity",
]
