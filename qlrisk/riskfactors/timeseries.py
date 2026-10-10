"""
QLRisk - Risk Factor Time Series
================================

Historical levels of risk factors (dates x factors), return computation
with per-factor conventions, gap filling, proxying, CSV persistence and
conversion back into MarketData snapshots.

Default return conventions by factor kind:

    RATE, SPREAD, DIVIDEND, SCALAR  -> ABSOLUTE   (x[t+h] - x[t])
    SPOT, PRICE, VOLATILITY         -> LOG        (ln(x[t+h] / x[t]))

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import csv
from datetime import date
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np

from .mapping import enumerate_risk_factors, get_factor_value
from .shocks import Shock, ShockType, set_factors
from .taxonomy import FactorKind, RiskFactorKey, RiskFactorLike, as_key

DEFAULT_RETURN_TYPES: Dict[FactorKind, ShockType] = {
    FactorKind.RATE: ShockType.ABSOLUTE,
    FactorKind.SPREAD: ShockType.ABSOLUTE,
    FactorKind.DIVIDEND: ShockType.ABSOLUTE,
    FactorKind.SCALAR: ShockType.ABSOLUTE,
    FactorKind.SPOT: ShockType.LOG,
    FactorKind.PRICE: ShockType.LOG,
    FactorKind.VOLATILITY: ShockType.LOG,
}


def _compute_return(start: np.ndarray, end: np.ndarray, return_type: ShockType) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        if return_type is ShockType.ABSOLUTE:
            out = end - start
        elif return_type is ShockType.RELATIVE:
            out = end / start - 1.0
        else:
            out = np.log(end / start)
    out = np.asarray(out, dtype=float)
    out[~np.isfinite(out)] = np.nan
    return out


def apply_return(level: float, ret: float, return_type: ShockType, inverse: bool = False) -> float:
    if return_type is ShockType.ABSOLUTE:
        return level - ret if inverse else level + ret
    if return_type is ShockType.RELATIVE:
        return level / (1.0 + ret) if inverse else level * (1.0 + ret)
    return level * np.exp(-ret if inverse else ret)


class RiskFactorTimeSeries:
    """
    Immutable panel of risk-factor levels: one row per date, one column per factor.

    Missing observations are NaN. Methods that change data return a new instance.
    """

    def __init__(
        self,
        dates: Sequence[date],
        factors: Sequence[RiskFactorLike],
        values: Union[np.ndarray, Sequence[Sequence[float]]],
    ):
        keys = [as_key(f) for f in factors]
        data = np.array(values, dtype=float, copy=True)
        if data.ndim != 2 or data.shape != (len(dates), len(keys)):
            raise ValueError(f"values shape {data.shape} does not match ({len(dates)} dates, {len(keys)} factors)")
        if len(set(dates)) != len(dates):
            raise ValueError("Duplicate dates in time series")
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate risk factors in time series")
        order = np.argsort(np.array(dates, dtype="datetime64[D]"), kind="stable")
        self._dates: List[date] = [dates[i] for i in order]
        self._factors: List[RiskFactorKey] = keys
        self._values = data[order]
        self._values.setflags(write=False)
        self._index = {k: i for i, k in enumerate(keys)}
        self._date_index = {d: i for i, d in enumerate(self._dates)}

    # ------------------------------------------------------------------ build

    @classmethod
    def from_snapshots(
        cls,
        snapshots: Union[Mapping[date, Any], Iterable[Tuple[date, Any]]],
        factors: Optional[Sequence[RiskFactorLike]] = None,
    ) -> "RiskFactorTimeSeries":
        """Build from MarketData snapshots; factors default to the union present in all snapshots."""
        items = list(snapshots.items()) if isinstance(snapshots, Mapping) else list(snapshots)
        if factors is None:
            seen = {}
            for _, md in items:
                for key in enumerate_risk_factors(md):
                    seen.setdefault(key, None)
            keys = sorted(seen, key=RiskFactorKey.sort_key)
        else:
            keys = [as_key(f) for f in factors]
        values = np.full((len(items), len(keys)), np.nan)
        for row, (_, md) in enumerate(items):
            for col, key in enumerate(keys):
                try:
                    values[row, col] = get_factor_value(md, key)
                except (KeyError, AttributeError, TypeError):
                    pass
        return cls([d for d, _ in items], keys, values)

    @classmethod
    def from_records(cls, records: Mapping[date, Mapping[RiskFactorLike, float]]) -> "RiskFactorTimeSeries":
        """Build from {date: {factor: level}}; absent entries become NaN."""
        keys: Dict[RiskFactorKey, None] = {}
        for levels in records.values():
            for f in levels:
                keys.setdefault(as_key(f), None)
        ordered = sorted(keys, key=RiskFactorKey.sort_key)
        col = {k: i for i, k in enumerate(ordered)}
        dates = list(records)
        values = np.full((len(dates), len(ordered)), np.nan)
        for row, d in enumerate(dates):
            for f, v in records[d].items():
                values[row, col[as_key(f)]] = v
        return cls(dates, ordered, values)

    # ------------------------------------------------------------- accessors

    @property
    def dates(self) -> List[date]:
        return list(self._dates)

    @property
    def factors(self) -> List[RiskFactorKey]:
        return list(self._factors)

    @property
    def values(self) -> np.ndarray:
        """Read-only (n_dates, n_factors) array."""
        return self._values

    @property
    def shape(self) -> Tuple[int, int]:
        return self._values.shape

    def __len__(self) -> int:
        return len(self._dates)

    def __repr__(self) -> str:
        span = f"{self._dates[0]}..{self._dates[-1]}" if self._dates else "empty"
        return f"RiskFactorTimeSeries({len(self._dates)} dates, {len(self._factors)} factors, {span})"

    def column(self, factor: RiskFactorLike) -> int:
        return self._index[as_key(factor)]

    def series(self, factor: RiskFactorLike) -> np.ndarray:
        """Levels of one factor over time."""
        return self._values[:, self.column(factor)].copy()

    def levels_at(self, on: date) -> Dict[RiskFactorKey, float]:
        """All non-missing levels on a date."""
        row = self._values[self._date_index[on]]
        return {k: float(v) for k, v in zip(self._factors, row) if not np.isnan(v)}

    def missing_counts(self) -> Dict[RiskFactorKey, int]:
        """Number of NaN observations per factor (only factors with gaps)."""
        counts = np.isnan(self._values).sum(axis=0)
        return {k: int(c) for k, c in zip(self._factors, counts) if c}

    # ------------------------------------------------------------ transforms

    def _with(self, dates=None, factors=None, values=None) -> "RiskFactorTimeSeries":
        return RiskFactorTimeSeries(
            self._dates if dates is None else dates,
            self._factors if factors is None else factors,
            self._values if values is None else values,
        )

    def select(self, factors: Iterable[RiskFactorLike]) -> "RiskFactorTimeSeries":
        """Subset of factors, in the given order."""
        keys = [as_key(f) for f in factors]
        return self._with(factors=keys, values=self._values[:, [self._index[k] for k in keys]])

    def window(self, start: Optional[date] = None, end: Optional[date] = None) -> "RiskFactorTimeSeries":
        """Dates within [start, end] inclusive."""
        rows = [i for i, d in enumerate(self._dates) if (start is None or d >= start) and (end is None or d <= end)]
        return self._with(dates=[self._dates[i] for i in rows], values=self._values[rows])

    def append(self, on: date, levels: Mapping[RiskFactorLike, float]) -> "RiskFactorTimeSeries":
        """New series with one more date; factors not in `levels` are NaN."""
        if on in self._date_index:
            raise ValueError(f"Date {on} already present")
        row = np.full(len(self._factors), np.nan)
        for f, v in levels.items():
            row[self._index[as_key(f)]] = v
        return self._with(dates=self._dates + [on], values=np.vstack([self._values, row]))

    def fill_missing(self, method: str = "ffill") -> "RiskFactorTimeSeries":
        """
        Fill gaps. 'ffill' carries the last observation forward, then
        back-fills any leading gap; 'interpolate' is linear in row index
        with flat ends.
        """
        out = self._values.copy()
        for col in range(out.shape[1]):
            series = out[:, col]
            valid = ~np.isnan(series)
            if valid.all() or not valid.any():
                continue
            idx = np.arange(len(series))
            if method == "interpolate":
                out[:, col] = np.interp(idx, idx[valid], series[valid])
            elif method == "ffill":
                last = np.maximum.accumulate(np.where(valid, idx, -1))
                filled = np.where(last >= 0, series[np.maximum(last, 0)], np.nan)
                first = idx[valid][0]
                filled[:first] = series[first]
                out[:, col] = filled
            else:
                raise ValueError(f"Unknown fill method: {method}")
        return self._with(values=out)

    def proxy(
        self,
        target: RiskFactorLike,
        source: RiskFactorLike,
        beta: float = 1.0,
        return_types: Optional[Mapping[RiskFactorLike, ShockType]] = None,
    ) -> "RiskFactorTimeSeries":
        """
        Fill the target's gaps by replaying `beta` x the source's returns
        from the nearest observed target level (forwards, then backwards
        for any leading gap).
        """
        t_key, s_key = as_key(target), as_key(source)
        t_type = self.return_types(return_types)[self._index[t_key]]
        s_type = self.return_types(return_types)[self._index[s_key]]
        tgt = self._values[:, self._index[t_key]].copy()
        src = self._values[:, self._index[s_key]]
        if not np.isnan(tgt).any():
            return self
        if np.isnan(tgt).all():
            raise ValueError(f"Target {t_key} has no observations to anchor the proxy")
        src_ret = np.concatenate([[np.nan], _compute_return(src[:-1], src[1:], s_type)])
        for i in range(1, len(tgt)):
            if np.isnan(tgt[i]) and not np.isnan(tgt[i - 1]) and not np.isnan(src_ret[i]):
                tgt[i] = apply_return(tgt[i - 1], beta * src_ret[i], t_type)
        for i in range(len(tgt) - 2, -1, -1):
            if np.isnan(tgt[i]) and not np.isnan(tgt[i + 1]) and not np.isnan(src_ret[i + 1]):
                tgt[i] = apply_return(tgt[i + 1], beta * src_ret[i + 1], t_type, inverse=True)
        values = self._values.copy()
        values[:, self._index[t_key]] = tgt
        return self._with(values=values)

    # --------------------------------------------------------------- returns

    def return_types(self, overrides: Optional[Mapping[RiskFactorLike, ShockType]] = None) -> List[ShockType]:
        """Return convention per factor (defaults by FactorKind, then overrides)."""
        types = [DEFAULT_RETURN_TYPES[k.kind] for k in self._factors]
        for f, t in (overrides or {}).items():
            types[self._index[as_key(f)]] = t
        return types

    def returns(
        self,
        horizon: int = 1,
        overlapping: bool = True,
        return_types: Optional[Mapping[RiskFactorLike, ShockType]] = None,
    ) -> Tuple[List[date], np.ndarray]:
        """
        Multi-day returns.

        Args:
            horizon: Holding period in observations (e.g. 10 for 10-day returns)
            overlapping: Step 1 observation (overlapping windows) or `horizon`
            return_types: Per-factor overrides of the return convention

        Returns:
            (end dates, array of shape (n_returns, n_factors)); NaN where a level is missing
        """
        if horizon < 1:
            raise ValueError("horizon must be >= 1")
        n = len(self._dates)
        if n <= horizon:
            return [], np.empty((0, len(self._factors)))
        step = 1 if overlapping else horizon
        ends = np.arange(horizon, n, step)
        start, end = self._values[ends - horizon], self._values[ends]
        out = np.empty_like(start)
        types = self.return_types(return_types)
        for t in set(types):
            cols = [i for i, ti in enumerate(types) if ti is t]
            out[:, cols] = _compute_return(start[:, cols], end[:, cols], t)
        return [self._dates[i] for i in ends], out

    def return_shocks(
        self,
        returns_row: Sequence[float],
        return_types: Optional[Mapping[RiskFactorLike, ShockType]] = None,
    ) -> List[Shock]:
        """Turn one row of `returns()` into shocks (NaN entries are skipped)."""
        types = self.return_types(return_types)
        return [
            Shock(k, float(r), t)
            for k, r, t in zip(self._factors, returns_row, types)
            if not np.isnan(r)
        ]

    # ---------------------------------------------------------- market data

    def market_data_at(self, on: date, template: Any) -> Any:
        """
        Copy of `template` with every factor of this series set to its level on `on`.

        Factors not present in the template are skipped. The copy's
        valuation_date is set to `on`.
        """
        present = set(enumerate_risk_factors(template))
        md = set_factors(template, {k: v for k, v in self.levels_at(on).items() if k in present})
        md.valuation_date = on
        return md

    # ----------------------------------------------------------- persistence

    def to_csv(self, path: str) -> None:
        """Write as CSV: first column 'date', one column per factor (string key)."""
        with open(path, "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["date"] + [str(k) for k in self._factors])
            for d, row in zip(self._dates, self._values):
                writer.writerow([d.isoformat()] + ["" if np.isnan(v) else repr(float(v)) for v in row])

    @classmethod
    def from_csv(cls, path: str) -> "RiskFactorTimeSeries":
        """Read the format written by to_csv."""
        with open(path, newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            dates, rows = [], []
            for line in reader:
                dates.append(date.fromisoformat(line[0]))
                rows.append([float(x) if x else np.nan for x in line[1:]])
        return cls(dates, header[1:], np.array(rows, dtype=float).reshape(len(dates), len(header) - 1))


__all__ = ["RiskFactorTimeSeries", "DEFAULT_RETURN_TYPES", "apply_return"]
