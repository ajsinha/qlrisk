"""
QLRisk - Sensitivity Results
============================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from ..riskfactors.taxonomy import RiskClass, RiskFactorKey, RiskFactorLike, as_key
from .ladders import TenorLadder, build_ladders
from .measures import Sensitivity, SensitivityMeasure

_GROUPERS = {
    "trade_id": lambda r: r.trade_id,
    "factor": lambda r: r.factor,
    "risk_class": lambda r: r.risk_class,
    "measure": lambda r: r.measure,
    "field": lambda r: r.factor.field if r.factor else None,
    "curve": lambda r: r.factor.curve_id if r.factor else None,
    "tenor": lambda r: r.factor.tenor if r.factor else None,
}

_FIRST_ORDER_EXCLUDED = (SensitivityMeasure.THETA, SensitivityMeasure.CROSS_GAMMA)


@dataclass
class SensitivityError:
    """A pricing failure during a sensitivity run (the run continues)."""
    trade_id: str
    factor: Optional[RiskFactorKey]
    message: str


@dataclass
class SensitivityResult:
    """
    Output of SensitivityEngine.compute().

    Attributes:
        records: One Sensitivity per (trade, factor), plus THETA / CROSS_GAMMA records if requested
        base_pv: Base PV per trade (in `currency`, or each trade's own currency)
        currency: Reporting currency, or None if values are in trade currencies
        errors: Pricing failures (trade skipped for that factor)
    """
    records: List[Sensitivity] = field(default_factory=list)
    base_pv: Dict[str, float] = field(default_factory=dict)
    currency: Optional[str] = None
    errors: List[SensitivityError] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.records)

    def __iter__(self):
        return iter(self.records)

    def __repr__(self) -> str:
        trades = len({r.trade_id for r in self.records})
        factors = len({r.factor for r in self.records if r.factor is not None})
        return (f"SensitivityResult({len(self.records)} records, {trades} trades, "
                f"{factors} factors, {len(self.errors)} errors)")

    # --------------------------------------------------------------- filters

    def filter(
        self,
        trade_id: Optional[str] = None,
        measure: Optional[SensitivityMeasure] = None,
        risk_class: Optional[RiskClass] = None,
        factor: Optional[RiskFactorLike] = None,
    ) -> List[Sensitivity]:
        key = as_key(factor) if factor is not None else None
        return [
            r for r in self.records
            if (trade_id is None or r.trade_id == trade_id)
            and (measure is None or r.measure is measure)
            and (risk_class is None or r.risk_class is risk_class)
            and (key is None or r.factor == key)
        ]

    def get(self, trade_id: str, factor: RiskFactorLike) -> Optional[Sensitivity]:
        """The first-order record for one trade and factor, if any."""
        key = as_key(factor)
        for r in self.records:
            if r.trade_id == trade_id and r.factor == key and r.measure not in _FIRST_ORDER_EXCLUDED:
                return r
        return None

    # ----------------------------------------------------------- aggregation

    def aggregate(
        self,
        by: Union[str, Sequence[str]] = ("risk_class", "measure"),
        value: str = "value",
        include: Optional[Sequence[SensitivityMeasure]] = None,
    ) -> Dict[Any, float]:
        """
        Sum `value` (or 'gamma') grouped by one or more of:
        trade_id, factor, risk_class, measure, field, curve, tenor.

        THETA and CROSS_GAMMA are excluded unless listed in `include`.
        Single-key grouping returns plain keys; multi-key returns tuples.
        """
        names = [by] if isinstance(by, str) else list(by)
        for n in names:
            if n not in _GROUPERS:
                raise ValueError(f"Cannot group by {n!r}; choose from {sorted(_GROUPERS)}")
        out: Dict[Any, float] = {}
        for r in self.records:
            if include is not None:
                if r.measure not in include:
                    continue
            elif r.measure in _FIRST_ORDER_EXCLUDED:
                continue
            amount = getattr(r, value)
            if amount is None:
                continue
            group = tuple(_GROUPERS[n](r) for n in names)
            group = group[0] if len(group) == 1 else group
            out[group] = out.get(group, 0.0) + amount
        return out

    def by_factor(self) -> Dict[RiskFactorKey, float]:
        """Portfolio first-order sensitivity per risk factor."""
        return self.aggregate("factor")

    def total(
        self,
        measure: Optional[SensitivityMeasure] = None,
        risk_class: Optional[RiskClass] = None,
    ) -> float:
        """Sum of first-order values, optionally for one measure / risk class."""
        return sum(
            r.value for r in self.records
            if r.measure not in _FIRST_ORDER_EXCLUDED
            and (measure is None or r.measure is measure)
            and (risk_class is None or r.risk_class is risk_class)
        )

    def theta(self) -> Dict[str, float]:
        """1-day theta per trade (empty unless computed)."""
        return {r.trade_id: r.value for r in self.records if r.measure is SensitivityMeasure.THETA}

    # ---------------------------------------------------------------- ladders

    def ladders(self, vertices: Optional[Sequence[float]] = None) -> Dict[Tuple, TenorLadder]:
        """All tenor ladders keyed by (field, name, measure)."""
        return build_ladders(self.records, vertices)

    def ladder(
        self,
        field: str,
        name: Optional[str] = None,
        measure: Optional[SensitivityMeasure] = None,
        vertices: Optional[Sequence[float]] = None,
    ) -> TenorLadder:
        """
        Ladder for one curve, e.g. ladder('forward_curves', 'SOFR') or ladder('discount_curve').

        If `measure` is omitted, the curve must have exactly one measure.
        """
        matches = [l for (f, n, m), l in self.ladders(vertices).items()
                   if f == field and n == name and (measure is None or m is measure)]
        if not matches:
            raise KeyError(f"No tenored sensitivities for {field}/{name}")
        if len(matches) > 1:
            raise ValueError(f"{field}/{name} has several measures; pass measure=")
        return matches[0]

    # ---------------------------------------------------------------- export

    def to_rows(self) -> List[Dict[str, Any]]:
        """Flat list of dicts (one per record), ready for CSV / DataFrame."""
        return [r.to_dict() for r in self.records]

    def merge(self, other: "SensitivityResult") -> "SensitivityResult":
        """Combine two results (e.g. two books) into one."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot merge results in {self.currency} and {other.currency}")
        overlap = set(self.base_pv) & set(other.base_pv)
        if overlap:
            raise ValueError(f"Trades present in both results: {sorted(overlap)[:5]}")
        return SensitivityResult(
            records=self.records + other.records,
            base_pv={**self.base_pv, **other.base_pv},
            currency=self.currency,
            errors=self.errors + other.errors,
        )


__all__ = ["SensitivityResult", "SensitivityError"]
