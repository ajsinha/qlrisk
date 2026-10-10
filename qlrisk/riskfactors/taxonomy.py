"""
QLRisk - Risk Factor Taxonomy
=============================

Names every market input a product can depend on, so it can be read,
shocked, bumped and stored as a time series.

A RiskFactorKey points at one number inside a products.base.MarketData:

    IR.DISCOUNT.5Y          discount_curve[5.0]
    IR.FWD.SOFR.3M          forward_curves["SOFR"][0.25]
    IR.REF.SOFR             reference_rates["SOFR"]
    FX.EURUSD               fx_spots["EURUSD"]
    CR.ACME.5Y              credit_curves["ACME"][5.0]
    EQ.AAPL                 equity_prices["AAPL"]
    DIV.AAPL.1Y             dividend_curves["AAPL"][1.0]
    BOND.UST10Y             bond_prices["UST10Y"]
    VOL.swaption_vol        volatility_surfaces["swaption_vol"]            (flat)
    VOL.cap_vol.2Y          volatility_surfaces["cap_vol"][2.0]            (term)
    VOL.eq_vol.1Y.100       volatility_surfaces["eq_vol"][1.0][100.0]      (surface)
    MISC.sofr_rate          market_data.sofr_rate                          (ad-hoc attribute)

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple, Union


class RiskClass(Enum):
    """Risk class, aligned with the FRTB risk classes."""
    INTEREST_RATE = "IR"
    CREDIT = "CR"
    EQUITY = "EQ"
    COMMODITY = "CM"
    FX = "FX"
    OTHER = "OT"


class FactorKind(Enum):
    """What kind of quantity a risk factor is; drives bump and return conventions."""
    RATE = "rate"            # zero / reference rates
    SPREAD = "spread"        # credit spreads / hazard rates
    SPOT = "spot"            # FX spots
    PRICE = "price"          # equity, bond and commodity prices
    VOLATILITY = "vol"       # implied volatilities
    DIVIDEND = "dividend"    # dividend yields
    SCALAR = "scalar"        # anything else


@dataclass(frozen=True)
class FieldSpec:
    """How one MarketData field maps onto risk factors."""
    field: str
    prefix: str
    risk_class: Optional[RiskClass]   # None: inferred from the factor name
    kind: FactorKind
    named: bool                       # keyed by name (forward_curves) or not (discount_curve)
    tenored: bool                     # values are tenor curves


FIELD_SPECS: Dict[str, FieldSpec] = {
    spec.field: spec for spec in (
        FieldSpec("discount_curve", "IR.DISCOUNT", RiskClass.INTEREST_RATE, FactorKind.RATE, False, True),
        FieldSpec("forward_curves", "IR.FWD", RiskClass.INTEREST_RATE, FactorKind.RATE, True, True),
        FieldSpec("reference_rates", "IR.REF", RiskClass.INTEREST_RATE, FactorKind.RATE, True, False),
        FieldSpec("fx_spots", "FX", RiskClass.FX, FactorKind.SPOT, True, False),
        FieldSpec("credit_curves", "CR", RiskClass.CREDIT, FactorKind.SPREAD, True, True),
        FieldSpec("equity_prices", "EQ", RiskClass.EQUITY, FactorKind.PRICE, True, False),
        FieldSpec("dividend_curves", "DIV", RiskClass.EQUITY, FactorKind.DIVIDEND, True, True),
        FieldSpec("bond_prices", "BOND", RiskClass.CREDIT, FactorKind.PRICE, True, False),
        FieldSpec("commodity_prices", "CMDTY", RiskClass.COMMODITY, FactorKind.PRICE, True, False),
        FieldSpec("volatility_surfaces", "VOL", None, FactorKind.VOLATILITY, True, False),
    )
}

MISC_PREFIX = "MISC"
_PREFIX_TO_FIELD = {spec.prefix: spec.field for spec in FIELD_SPECS.values()}

# Volatility surface names are free-form; infer their risk class from the name.
_VOL_CLASS_HINTS: Tuple[Tuple[str, RiskClass], ...] = (
    ("swaption", RiskClass.INTEREST_RATE),
    ("cap", RiskClass.INTEREST_RATE),
    ("floor", RiskClass.INTEREST_RATE),
    ("ir", RiskClass.INTEREST_RATE),
    ("fx", RiskClass.FX),
    ("eq", RiskClass.EQUITY),
    ("stock", RiskClass.EQUITY),
    ("index", RiskClass.EQUITY),
    ("cds", RiskClass.CREDIT),
    ("credit", RiskClass.CREDIT),
    ("cm", RiskClass.COMMODITY),
    ("commodity", RiskClass.COMMODITY),
    ("oil", RiskClass.COMMODITY),
    ("gas", RiskClass.COMMODITY),
    ("gold", RiskClass.COMMODITY),
)


def format_tenor(tenor: float) -> str:
    """Format a tenor in years as a label: 0.25 -> '3M', 5.0 -> '5Y', 0.1 -> '0.1Y'."""
    if tenor < 1.0:
        months = tenor * 12.0
        if abs(months - round(months)) < 1e-9 and round(months) > 0:
            return f"{int(round(months))}M"
    if abs(tenor - round(tenor)) < 1e-9:
        return f"{int(round(tenor))}Y"
    return f"{tenor:g}Y"


def parse_tenor(label: str) -> float:
    """Parse a tenor label back into years: '3M' -> 0.25, '5Y' -> 5.0, '2W' -> 2/52, '10D' -> 10/365."""
    label = label.strip().upper()
    unit, number = label[-1], label[:-1]
    if unit == "Y":
        return float(number)
    if unit == "M":
        return float(number) / 12.0
    if unit == "W":
        return float(number) / 52.0
    if unit == "D":
        return float(number) / 365.0
    return float(label)


def infer_vol_risk_class(name: str) -> RiskClass:
    """Best-effort risk class for a volatility surface name such as 'swaption_vol' or 'fx_vol'."""
    lowered = name.lower()
    for hint, risk_class in _VOL_CLASS_HINTS:
        if lowered.startswith(hint) or f"_{hint}" in lowered:
            return risk_class
    return RiskClass.OTHER


@dataclass(frozen=True)
class RiskFactorKey:
    """
    Address of one shockable number inside a MarketData.

    Attributes:
        field: MarketData attribute name (e.g. 'forward_curves')
        name: Key within a named field (e.g. 'SOFR', 'EURUSD'); None for unnamed fields
        tenor: Tenor in years for curve pillars / vol term structures
        strike: Second dimension of a volatility surface
    """
    field: str
    name: Optional[str] = None
    tenor: Optional[float] = None
    strike: Optional[float] = None

    @property
    def spec(self) -> Optional[FieldSpec]:
        return FIELD_SPECS.get(self.field)

    @property
    def risk_class(self) -> RiskClass:
        spec = self.spec
        if spec is None:
            return RiskClass.OTHER
        if spec.risk_class is None:
            return infer_vol_risk_class(self.name or "")
        return spec.risk_class

    @property
    def kind(self) -> FactorKind:
        spec = self.spec
        return spec.kind if spec else FactorKind.SCALAR

    @property
    def curve_id(self) -> Tuple[str, Optional[str]]:
        """Identifies the curve/surface the factor belongs to (field, name)."""
        return (self.field, self.name)

    def __str__(self) -> str:
        spec = self.spec
        parts = [spec.prefix if spec else f"{MISC_PREFIX}.{self.field}"]
        if self.name is not None:
            parts.append(str(self.name))
        if self.tenor is not None:
            parts.append(format_tenor(self.tenor))
        if self.strike is not None:
            parts.append(f"{self.strike:g}")
        return ".".join(parts)

    def __repr__(self) -> str:
        return f"RiskFactorKey({self})"

    def sort_key(self) -> Tuple:
        return (
            self.risk_class.value, self.field, self.name or "",
            -1.0 if self.tenor is None else self.tenor,
            -1.0 if self.strike is None else self.strike,
        )

    @classmethod
    def parse(cls, text: str) -> "RiskFactorKey":
        """
        Parse the string form back into a key.

        Names containing '.' cannot be parsed from text; construct those
        keys directly.
        """
        parts = text.split(".")
        if parts[0] == MISC_PREFIX:
            if len(parts) < 2:
                raise ValueError(f"Invalid risk factor key: {text!r}")
            return cls(field=parts[1], name=parts[2] if len(parts) > 2 else None)

        for width in (2, 1):
            prefix = ".".join(parts[:width])
            if prefix in _PREFIX_TO_FIELD:
                spec = FIELD_SPECS[_PREFIX_TO_FIELD[prefix]]
                rest = parts[width:]
                break
        else:
            raise ValueError(f"Unknown risk factor prefix in {text!r}")

        name = None
        if spec.named:
            if not rest:
                raise ValueError(f"Risk factor {text!r} needs a name")
            name, rest = rest[0], rest[1:]
        tenor = parse_tenor(rest[0]) if rest else None
        strike = float(rest[1]) if len(rest) > 1 else None
        if len(rest) > 2:
            raise ValueError(f"Too many components in risk factor key {text!r}")
        return cls(field=spec.field, name=name, tenor=tenor, strike=strike)


RiskFactorLike = Union[RiskFactorKey, str]


def as_key(factor: RiskFactorLike) -> RiskFactorKey:
    """Accept either a RiskFactorKey or its string form."""
    return factor if isinstance(factor, RiskFactorKey) else RiskFactorKey.parse(factor)


__all__ = [
    "RiskClass", "FactorKind", "FieldSpec", "FIELD_SPECS", "RiskFactorKey",
    "RiskFactorLike", "as_key", "format_tenor", "parse_tenor", "infer_vol_risk_class",
]
