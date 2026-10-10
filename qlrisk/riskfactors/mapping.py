"""
QLRisk - Risk Factor Mapping
============================

Reads, writes and enumerates risk factors in a products.base.MarketData,
clones market data copy-on-write, and detects which risk factors a
product depends on.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import copy
import dataclasses
import math
from numbers import Real
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

from .taxonomy import FIELD_SPECS, RiskClass, RiskFactorKey, RiskFactorLike, as_key

# MarketData attributes that are never risk factors.
_NON_FACTOR_FIELDS = {"valuation_date", "correlation_matrix"}


def _is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def _find_key(container: Dict, wanted: Any) -> Any:
    """Exact dict key, or the float key within rounding distance of `wanted`."""
    if wanted in container:
        return wanted
    if _is_number(wanted):
        for key in container:
            if _is_number(key) and math.isclose(key, wanted, rel_tol=1e-9, abs_tol=1e-12):
                return key
    raise KeyError(wanted)


def _misc_fields(market_data: Any) -> List[str]:
    """Ad-hoc numeric attributes (e.g. `sofr_rate`) that are not part of FIELD_SPECS."""
    declared = {f.name for f in dataclasses.fields(market_data)} if dataclasses.is_dataclass(market_data) else set()
    names = []
    for name, value in vars(market_data).items():
        if name.startswith("_") or name in FIELD_SPECS or name in _NON_FACTOR_FIELDS:
            continue
        if name in declared and not (_is_number(value) or isinstance(value, dict)):
            continue
        if _is_number(value) or (isinstance(value, dict) and any(_is_number(v) for v in value.values())):
            names.append(name)
    return names


# =============================================================================
# Enumeration
# =============================================================================

def _vol_keys(name: str, surface: Any) -> List[RiskFactorKey]:
    field = "volatility_surfaces"
    if _is_number(surface):
        return [RiskFactorKey(field, name)]
    keys = []
    if isinstance(surface, dict):
        for tenor, value in surface.items():
            if not _is_number(tenor):
                continue
            if _is_number(value):
                keys.append(RiskFactorKey(field, name, float(tenor)))
            elif isinstance(value, dict):
                keys.extend(
                    RiskFactorKey(field, name, float(tenor), float(strike))
                    for strike, vol in value.items()
                    if _is_number(strike) and _is_number(vol)
                )
    return keys


def enumerate_risk_factors(
    market_data: Any,
    risk_classes: Optional[Iterable[RiskClass]] = None,
    fields: Optional[Iterable[str]] = None,
) -> List[RiskFactorKey]:
    """
    List every shockable number in the market data.

    Args:
        market_data: products.base.MarketData
        risk_classes: Optional filter on risk class
        fields: Optional filter on MarketData field names

    Returns:
        Sorted list of RiskFactorKey
    """
    keys: List[RiskFactorKey] = []
    for spec in FIELD_SPECS.values():
        value = getattr(market_data, spec.field, None)
        if not value:
            continue
        if spec.field == "volatility_surfaces":
            for name, surface in value.items():
                keys.extend(_vol_keys(name, surface))
        elif not spec.named:
            keys.extend(RiskFactorKey(spec.field, None, float(t)) for t, v in value.items() if _is_number(v))
        elif spec.tenored:
            for name, curve in value.items():
                if isinstance(curve, dict):
                    keys.extend(RiskFactorKey(spec.field, name, float(t)) for t, v in curve.items() if _is_number(v))
        else:
            keys.extend(RiskFactorKey(spec.field, name) for name, v in value.items() if _is_number(v))

    for name in _misc_fields(market_data):
        value = getattr(market_data, name)
        if _is_number(value):
            keys.append(RiskFactorKey(name))
        else:
            keys.extend(RiskFactorKey(name, str(k)) for k, v in value.items() if _is_number(v))

    if risk_classes is not None:
        wanted = set(risk_classes)
        keys = [k for k in keys if k.risk_class in wanted]
    if fields is not None:
        wanted_fields = set(fields)
        keys = [k for k in keys if k.field in wanted_fields]
    return sorted(keys, key=RiskFactorKey.sort_key)


# =============================================================================
# Get / set
# =============================================================================

def _locate(market_data: Any, key: RiskFactorKey) -> Tuple[Dict, Any]:
    """Return (container, dict_key) holding the factor value; ('attr', name) for scalar attributes."""
    spec = key.spec
    if spec is None:
        value = getattr(market_data, key.field)
        if key.name is None:
            return None, key.field
        return value, _find_key(value, key.name)

    container = getattr(market_data, key.field)
    if spec.named:
        container_key = _find_key(container, key.name)
        if key.tenor is None:
            return container, container_key
        container = container[container_key]
    if key.tenor is None:
        raise KeyError(f"{key} needs a tenor")
    tenor_key = _find_key(container, key.tenor)
    if key.strike is None:
        return container, tenor_key
    return container[tenor_key], _find_key(container[tenor_key], key.strike)


def get_factor_value(market_data: Any, factor: RiskFactorLike) -> float:
    """Read the current value of a risk factor."""
    container, slot = _locate(market_data, as_key(factor))
    return float(getattr(market_data, slot) if container is None else container[slot])


def set_factor_value(market_data: Any, factor: RiskFactorLike, value: float) -> None:
    """
    Overwrite a risk factor value **in place**.

    Call this on a clone (see `clone_market_data`), never on shared market data.
    """
    container, slot = _locate(market_data, as_key(factor))
    if container is None:
        setattr(market_data, slot, value)
    else:
        container[slot] = value


# =============================================================================
# Cloning
# =============================================================================

def _copy_nested(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _copy_nested(v) for k, v in value.items()}
    return value


def clone_market_data(market_data: Any, fields: Optional[Iterable[str]] = None) -> Any:
    """
    Copy-on-write clone.

    The returned object is independent in the requested `fields` (all
    shockable fields by default); every other attribute is shared with the
    original. Writing factors in the cloned fields never touches the base.
    """
    clone = copy.copy(market_data)
    if fields is None:
        fields = list(FIELD_SPECS) + _misc_fields(market_data)
    for name in set(fields):
        if hasattr(clone, name):
            setattr(clone, name, _copy_nested(getattr(market_data, name)))
    return clone


# =============================================================================
# Dependency detection
# =============================================================================

class _TrackingDict(dict):
    """dict that records which paths are read. `named` dicts record per-key; others record the whole path."""

    __slots__ = ("_record", "_path", "_named")

    def __init__(self, data: Dict, record: Callable[[Tuple], None], path: Tuple, named: bool):
        super().__init__(data)
        self._record = record
        self._path = path
        self._named = named

    def _touch(self, key: Any = None) -> None:
        if self._named and key is not None:
            self._record(self._path + (key,))
        else:
            self._record(self._path)

    def __getitem__(self, key):
        self._touch(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        self._touch(key)
        return super().get(key, default)

    def __contains__(self, key):
        self._touch(key)
        return super().__contains__(key)

    def __iter__(self):
        self._touch()
        return super().__iter__()

    def keys(self):
        self._touch()
        return super().keys()

    def values(self):
        self._touch()
        return super().values()

    def items(self):
        self._touch()
        return super().items()

    def __len__(self):
        self._touch()
        return super().__len__()


_TRACKING_CLASSES: Dict[type, type] = {}


def _tracking_class(cls: type) -> type:
    if cls not in _TRACKING_CLASSES:
        def __getattribute__(self, name):
            if not name.startswith("_"):
                object.__getattribute__(self, "_qlrisk_accessed").add(name)
            return object.__getattribute__(self, name)
        _TRACKING_CLASSES[cls] = type(f"Tracking{cls.__name__}", (cls,), {"__getattribute__": __getattribute__})
    return _TRACKING_CLASSES[cls]


def _make_tracking(market_data: Any) -> Tuple[Any, Set[Tuple], Set[str]]:
    paths: Set[Tuple] = set()
    accessed: Set[str] = set()
    tracked = object.__new__(_tracking_class(type(market_data)))
    tracked.__dict__.update(vars(market_data))
    tracked.__dict__["_qlrisk_accessed"] = accessed

    for spec in FIELD_SPECS.values():
        value = vars(market_data).get(spec.field)
        if not isinstance(value, dict):
            continue
        path = (spec.field,)
        if spec.named:
            inner = {
                name: (_TrackingDict(v, paths.add, path + (name,), named=False) if isinstance(v, dict) else v)
                for name, v in value.items()
            }
            tracked.__dict__[spec.field] = _TrackingDict(inner, paths.add, path, named=True)
        else:
            tracked.__dict__[spec.field] = _TrackingDict(value, paths.add, path, named=False)
    return tracked, paths, accessed


def detect_risk_factors(product: Any, market_data: Any) -> List[RiskFactorKey]:
    """
    Risk factors a product reads when it prices.

    Prices the product once against an access-recording copy of the market
    data. A read of any point on a curve or surface counts as a dependency on
    the whole curve/surface, because interpolation uses neighbouring pillars.
    Products whose code path depends on market levels may read more factors
    under shocked data; override `BaseProduct.risk_factors()` for those.
    """
    tracked, paths, accessed = _make_tracking(market_data)
    product.price(tracked)

    def depends(key: RiskFactorKey) -> bool:
        if key.spec is None:
            return key.field in accessed
        if (key.field,) in paths:
            return True
        return key.name is not None and (key.field, key.name) in paths

    return [key for key in enumerate_risk_factors(market_data) if depends(key)]


__all__ = [
    "enumerate_risk_factors", "get_factor_value", "set_factor_value",
    "clone_market_data", "detect_risk_factors",
]
