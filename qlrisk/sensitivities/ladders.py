"""
QLRisk - Tenor Ladders
======================

Groups tenored sensitivities by curve and re-buckets them onto a target
set of vertices. A sensitivity at a tenor between two vertices is split
between them linearly (the FRTB allocation rule); outside the vertex range
it goes to the nearest end vertex. Totals are preserved.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from bisect import bisect_right
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from ..riskfactors.taxonomy import format_tenor
from .measures import Sensitivity, SensitivityMeasure

STANDARD_TENORS: Tuple[float, ...] = (1 / 12, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 30.0)
FRTB_GIRR_VERTICES: Tuple[float, ...] = (0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0)
FRTB_CSR_VERTICES: Tuple[float, ...] = (0.5, 1.0, 3.0, 5.0, 10.0)
FRTB_VEGA_MATURITIES: Tuple[float, ...] = (0.5, 1.0, 3.0, 5.0, 10.0)


def rebucket(values: Mapping[float, float], vertices: Sequence[float]) -> Dict[float, float]:
    """
    Allocate tenor -> amount onto vertices by linear interpolation weights.

    Args:
        values: Amounts by tenor (years)
        vertices: Target vertices (any order)

    Returns:
        Amount by vertex (every vertex present, zero if nothing allocated)
    """
    verts = sorted(vertices)
    if not verts:
        raise ValueError("vertices must not be empty")
    out = {v: 0.0 for v in verts}
    for tenor, amount in values.items():
        if tenor <= verts[0]:
            out[verts[0]] += amount
        elif tenor >= verts[-1]:
            out[verts[-1]] += amount
        else:
            i = bisect_right(verts, tenor)
            lo, hi = verts[i - 1], verts[i]
            w = (tenor - lo) / (hi - lo)
            out[lo] += amount * (1.0 - w)
            out[hi] += amount * w
    return out


@dataclass
class TenorLadder:
    """Sensitivities of one curve (field, name) by tenor."""
    curve: Tuple[str, Optional[str]]
    measure: SensitivityMeasure
    values: Dict[float, float] = field(default_factory=dict)

    @property
    def total(self) -> float:
        return sum(self.values.values())

    def rows(self) -> List[Tuple[str, float]]:
        """(tenor label, value) sorted by tenor."""
        return [(format_tenor(t), v) for t, v in sorted(self.values.items())]

    def rebucket(self, vertices: Sequence[float]) -> "TenorLadder":
        return TenorLadder(self.curve, self.measure, rebucket(self.values, vertices))

    def __str__(self) -> str:
        field_name, name = self.curve
        title = f"{field_name}{'/' + name if name else ''} {self.measure.value}"
        body = "\n".join(f"  {label:>6}  {value:>16,.2f}" for label, value in self.rows())
        return f"{title}\n{body}\n  {'total':>6}  {self.total:>16,.2f}"


def build_ladders(
    records: Iterable[Sensitivity],
    vertices: Optional[Sequence[float]] = None,
) -> Dict[Tuple[str, Optional[str], SensitivityMeasure], TenorLadder]:
    """
    One ladder per (field, curve name, measure) from first-order tenored sensitivities.

    Volatility surface points with a strike are summed across strikes per tenor.

    Args:
        records: Sensitivity records (THETA / CROSS_GAMMA and untenored factors are ignored)
        vertices: Optional vertices to re-bucket onto; native pillars when None
    """
    ladders: Dict[Tuple[str, Optional[str], SensitivityMeasure], TenorLadder] = {}
    for rec in records:
        f = rec.factor
        if f is None or f.tenor is None or rec.measure in (SensitivityMeasure.THETA, SensitivityMeasure.CROSS_GAMMA):
            continue
        key = (f.field, f.name, rec.measure)
        ladder = ladders.setdefault(key, TenorLadder((f.field, f.name), rec.measure))
        ladder.values[f.tenor] = ladder.values.get(f.tenor, 0.0) + rec.value
    if vertices is not None:
        ladders = {k: l.rebucket(vertices) for k, l in ladders.items()}
    return ladders


__all__ = [
    "STANDARD_TENORS", "FRTB_GIRR_VERTICES", "FRTB_CSR_VERTICES", "FRTB_VEGA_MATURITIES",
    "rebucket", "TenorLadder", "build_ladders",
]
