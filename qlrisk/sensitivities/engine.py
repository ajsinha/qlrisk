"""
QLRisk - Sensitivity Engine
===========================

Bump-and-reprice sensitivities for any BaseProduct.

For each risk factor the engine builds the bumped market data once and
reprices only the products that depend on that factor (dependencies are
detected automatically via BaseProduct.risk_factors()).

    from qlrisk.sensitivities import SensitivityEngine

    result = SensitivityEngine().compute(products, market_data, reporting_currency="USD")
    print(result.ladder("forward_curves", "SOFR"))       # DV01 by tenor
    print(result.aggregate(("risk_class", "measure")))

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from itertools import combinations
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from ..riskfactors.mapping import enumerate_risk_factors, get_factor_value
from ..riskfactors.shocks import Shock, apply_shocks
from ..riskfactors.taxonomy import FactorKind, RiskClass, RiskFactorKey, RiskFactorLike, as_key
from .measures import DEFAULT_BUMPS, BumpSpec, Sensitivity, SensitivityMeasure, measure_for
from .results import SensitivityError, SensitivityResult

CENTRAL = "central"
FORWARD = "forward"


def _currency_code(currency: Any) -> str:
    return getattr(currency, "value", currency)


def fx_convert(market_data: Any, amount: float, from_ccy: str, to_ccy: str) -> float:
    """
    Convert an amount using market_data.fx_spots ('EURUSD' = USD per EUR).

    Tries the direct pair, the inverse pair, then triangulation via USD.
    """
    if from_ccy == to_ccy:
        return amount
    spots = market_data.fx_spots
    if f"{from_ccy}{to_ccy}" in spots:
        return amount * spots[f"{from_ccy}{to_ccy}"]
    if f"{to_ccy}{from_ccy}" in spots:
        return amount / spots[f"{to_ccy}{from_ccy}"]
    if "USD" not in (from_ccy, to_ccy):
        return fx_convert(market_data, fx_convert(market_data, amount, from_ccy, "USD"), "USD", to_ccy)
    raise KeyError(f"No FX rate to convert {from_ccy} to {to_ccy}")


def fx_pairs_used(market_data: Any, from_ccy: str, to_ccy: str) -> List[str]:
    """The fx_spots keys fx_convert() reads for this conversion."""
    if from_ccy == to_ccy:
        return []
    spots = market_data.fx_spots
    for pair in (f"{from_ccy}{to_ccy}", f"{to_ccy}{from_ccy}"):
        if pair in spots:
            return [pair]
    if "USD" not in (from_ccy, to_ccy):
        return fx_pairs_used(market_data, from_ccy, "USD") + fx_pairs_used(market_data, "USD", to_ccy)
    return []


class SensitivityEngine:
    """
    Bump-and-reprice sensitivity calculator.

    Args:
        bumps: Per-FactorKind overrides of DEFAULT_BUMPS
        method: 'central' (first + second order, 2 repricings per factor)
                or 'forward' (first order only, 1 repricing per factor)
        max_workers: Threads used across factors. 1 runs sequentially; pure-Python
                     pricers gain little from threads, QuantLib-backed pricers can.
        detect_dependencies: Reprice only products that read a factor (recommended).
                             False reprices every product for every factor.
    """

    def __init__(
        self,
        bumps: Optional[Mapping[FactorKind, BumpSpec]] = None,
        method: str = CENTRAL,
        max_workers: int = 1,
        detect_dependencies: bool = True,
    ):
        if method not in (CENTRAL, FORWARD):
            raise ValueError(f"method must be '{CENTRAL}' or '{FORWARD}'")
        self.bumps: Dict[FactorKind, BumpSpec] = {**DEFAULT_BUMPS, **(bumps or {})}
        self.method = method
        self.max_workers = max(1, int(max_workers))
        self.detect_dependencies = detect_dependencies

    # ------------------------------------------------------------------ public

    def compute(
        self,
        products: Union[Any, Sequence[Any]],
        market_data: Any,
        factors: Optional[Iterable[RiskFactorLike]] = None,
        risk_classes: Optional[Iterable[RiskClass]] = None,
        reporting_currency: Optional[str] = None,
        include_theta: bool = False,
    ) -> SensitivityResult:
        """
        Compute first- (and with central differences second-) order sensitivities.

        Args:
            products: One product or a sequence of products (unique trade_ids)
            market_data: Base products.base.MarketData (never modified)
            factors: Restrict to these factors; default all factors in the market data
            risk_classes: Restrict to these risk classes
            reporting_currency: Convert PVs (base and bumped) into this currency using
                                the same market data's FX spots, so FX factors also
                                capture translation risk. None keeps trade currencies.
            include_theta: Add a THETA record per trade (1 calendar day roll, same market data)
        """
        book = self._as_book(products)
        result = SensitivityResult(currency=reporting_currency)

        base_pv, pv_currency = {}, {}
        for trade_id, product in book.items():
            pv = self._pv(product, market_data, reporting_currency, result, None, pv_currency)
            if pv is not None:
                base_pv[trade_id] = pv
        result.base_pv = dict(base_pv)
        live = {t: p for t, p in book.items() if t in base_pv}

        candidates = self._candidate_factors(market_data, factors, risk_classes)
        dependents = self._dependents(live, market_data, candidates, result)
        if reporting_currency:
            # Converting PVs into the reporting currency adds FX translation risk.
            for trade_id in live:
                for pair in fx_pairs_used(market_data, pv_currency[trade_id], reporting_currency):
                    key = RiskFactorKey("fx_spots", pair)
                    if key in dependents and trade_id not in dependents[key]:
                        dependents[key].append(trade_id)

        jobs = [(f, trades) for f, trades in dependents.items() if trades]
        for records in self._map(lambda job: self._bump_factor(job[0], job[1], live, market_data, base_pv,
                                                               reporting_currency, result), jobs):
            result.records.extend(records)

        if include_theta:
            rolled = copy.copy(market_data)
            rolled.valuation_date = market_data.valuation_date + timedelta(days=1)
            for trade_id, product in live.items():
                pv = self._pv(product, rolled, reporting_currency, result, None)
                if pv is not None:
                    result.records.append(Sensitivity(
                        trade_id, None, SensitivityMeasure.THETA, pv - base_pv[trade_id],
                        currency=reporting_currency or self._trade_currency(product),
                    ))

        result.records.sort(key=lambda r: (r.trade_id, r.factor.sort_key() if r.factor else ()))
        return result

    def cross_gamma(
        self,
        products: Union[Any, Sequence[Any]],
        market_data: Any,
        factors: Sequence[RiskFactorLike],
        reporting_currency: Optional[str] = None,
    ) -> SensitivityResult:
        """
        Mixed second-order sensitivities for every pair of `factors`:
        (PV(++) - PV(+-) - PV(-+) + PV(--)) / 4, per bump_i x bump_j.

        Cost is 4 repricings per pair; pass a short, targeted factor list.
        """
        book = self._as_book(products)
        keys = [as_key(f) for f in factors]
        result = SensitivityResult(currency=reporting_currency)
        for trade_id, product in book.items():
            pv = self._pv(product, market_data, reporting_currency, result, None)
            if pv is not None:
                result.base_pv[trade_id] = pv

        def pair(job: Tuple[RiskFactorKey, RiskFactorKey]) -> List[Sensitivity]:
            fi, fj = job
            bi, bj = self.bumps[fi.kind], self.bumps[fj.kind]
            corners = {}
            for si in (1, -1):
                for sj in (1, -1):
                    corners[(si, sj)] = apply_shocks(market_data, [
                        Shock(fi, si * bi.size, bi.shock_type), Shock(fj, sj * bj.size, bj.shock_type)])
            out = []
            for trade_id in result.base_pv:
                product = book[trade_id]
                pvs = {c: self._pv(product, md, reporting_currency, result, fi) for c, md in corners.items()}
                if any(v is None for v in pvs.values()):
                    continue
                value = (pvs[(1, 1)] - pvs[(1, -1)] - pvs[(-1, 1)] + pvs[(-1, -1)]) / 4.0
                out.append(Sensitivity(
                    trade_id, fi, SensitivityMeasure.CROSS_GAMMA, value, factor2=fj,
                    currency=reporting_currency or self._trade_currency(product),
                ))
            return out

        for records in self._map(pair, list(combinations(keys, 2))):
            result.records.extend(records)
        return result

    # ----------------------------------------------------------------- helpers

    @staticmethod
    def _as_book(products: Union[Any, Sequence[Any]]) -> Dict[str, Any]:
        items = list(products) if isinstance(products, (list, tuple)) else [products]
        book: Dict[str, Any] = {}
        for p in items:
            if p.trade_id in book:
                raise ValueError(f"Duplicate trade_id: {p.trade_id}")
            book[p.trade_id] = p
        return book

    @staticmethod
    def _trade_currency(product: Any) -> str:
        return _currency_code(product.currency)

    def _map(self, fn, jobs: List) -> Iterable:
        if self.max_workers == 1 or len(jobs) < 2:
            return map(fn, jobs)
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            return list(pool.map(fn, jobs))

    def _pv(
        self,
        product: Any,
        market_data: Any,
        reporting_currency: Optional[str],
        result: SensitivityResult,
        factor: Optional[RiskFactorKey],
        currency_out: Optional[Dict[str, str]] = None,
    ) -> Optional[float]:
        try:
            priced = product.price(market_data)
            pv = float(priced.npv)
            if currency_out is not None:
                currency_out[product.trade_id] = _currency_code(priced.currency)
            if reporting_currency:
                pv = fx_convert(market_data, pv, _currency_code(priced.currency), reporting_currency)
            return pv
        except Exception as exc:  # one bad trade must not stop the run
            result.errors.append(SensitivityError(product.trade_id, factor, f"{type(exc).__name__}: {exc}"))
            return None

    @staticmethod
    def _candidate_factors(
        market_data: Any,
        factors: Optional[Iterable[RiskFactorLike]],
        risk_classes: Optional[Iterable[RiskClass]],
    ) -> List[RiskFactorKey]:
        keys = [as_key(f) for f in factors] if factors is not None else enumerate_risk_factors(market_data)
        if risk_classes is not None:
            wanted = set(risk_classes)
            keys = [k for k in keys if k.risk_class in wanted]
        return keys

    def _dependents(
        self,
        book: Dict[str, Any],
        market_data: Any,
        candidates: List[RiskFactorKey],
        result: SensitivityResult,
    ) -> Dict[RiskFactorKey, List[str]]:
        dependents: Dict[RiskFactorKey, List[str]] = {k: [] for k in candidates}
        for trade_id, product in book.items():
            if not self.detect_dependencies:
                deps = candidates
            else:
                try:
                    deps = product.risk_factors(market_data)
                except Exception as exc:
                    result.errors.append(SensitivityError(trade_id, None, f"dependency detection failed: {exc}"))
                    deps = candidates
            for key in deps:
                if key in dependents:
                    dependents[key].append(trade_id)
        return dependents

    def _bump_factor(
        self,
        factor: RiskFactorKey,
        trade_ids: List[str],
        book: Dict[str, Any],
        market_data: Any,
        base_pv: Dict[str, float],
        reporting_currency: Optional[str],
        result: SensitivityResult,
    ) -> List[Sensitivity]:
        bump = self.bumps[factor.kind]
        level = get_factor_value(market_data, factor)
        step = bump.bump_in_factor_units(level)
        up = apply_shocks(market_data, [Shock(factor, bump.size, bump.shock_type)])
        down = apply_shocks(market_data, [Shock(factor, -bump.size, bump.shock_type)]) if self.method == CENTRAL else None
        measure = measure_for(factor)

        records = []
        for trade_id in trade_ids:
            product = book[trade_id]
            pv_up = self._pv(product, up, reporting_currency, result, factor)
            if pv_up is None:
                continue
            pv0 = base_pv[trade_id]
            if down is not None:
                pv_down = self._pv(product, down, reporting_currency, result, factor)
                if pv_down is None:
                    continue
                first = (pv_up - pv_down) / 2.0
                second = pv_up - 2.0 * pv0 + pv_down
            else:
                first, second = pv_up - pv0, None
            records.append(Sensitivity(
                trade_id=trade_id,
                factor=factor,
                measure=measure,
                value=first,
                gamma=second,
                derivative=first / step if step else None,
                bump_size=bump.size,
                bump_type=bump.shock_type,
                currency=reporting_currency or self._trade_currency(product),
            ))
        return records


def compute_sensitivities(products: Union[Any, Sequence[Any]], market_data: Any, **kwargs) -> SensitivityResult:
    """Convenience wrapper: SensitivityEngine(**engine options).compute(...)."""
    engine_keys = {"bumps", "method", "max_workers", "detect_dependencies"}
    engine = SensitivityEngine(**{k: v for k, v in kwargs.items() if k in engine_keys})
    return engine.compute(products, market_data, **{k: v for k, v in kwargs.items() if k not in engine_keys})


__all__ = ["SensitivityEngine", "compute_sensitivities", "fx_convert", "fx_pairs_used", "CENTRAL", "FORWARD"]
