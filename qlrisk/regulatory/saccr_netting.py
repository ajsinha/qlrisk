"""
QLRisk - SA-CCR Netting-Set Aggregation (Basel CRE52)
====================================================

    result = saccr_netting_sets(trades, market_data, csa={"BANK-A": CSATerms(margined=True, collateral=2e6)})

Trade-level add-ons come from each product's calculate_saccr() (supervisory factor x supervisory
delta x adjusted notional x maturity factor). Each add-on is signed by the direction of the trade's
primary risk (sign of dPV / d(primary risk factor) from the SensitivityEngine), then aggregated:

  Interest rate: hedging set = currency; maturity buckets <1y, 1-5y, >5y
      EffNotional = sqrt(D1^2 + D2^2 + D3^2 + 1.4 D1 D2 + 1.4 D2 D3 + 0.6 D1 D3)
  FX: hedging set = currency pair; AddOn = |sum D|
  Credit / Equity: per entity A_k = sum D (signed); AddOn = sqrt((sum rho A_k)^2 + sum (1 - rho^2) A_k^2),
      rho = 50% (single name) / 80% (index: names listed in `index_names`)
  Commodity: hedging sets energy / metals / agricultural / other; per commodity type A_k = sum D;
      AddOn_HS = sqrt((0.4 sum A_k)^2 + 0.84 sum A_k^2); summed over hedging sets
  Netting set: V = sum MtM, C = net collateral (haircut)
      unmargined RC = max(V - C, 0);  margined RC = max(V - C, TH + MTA - NICA, 0)
      margined maturity factor 1.5 sqrt(MPOR / 250) replaces sqrt(min(M, 1)) trade by trade
      multiplier = min(1, 0.05 + 0.95 exp((V - C) / (2 x 0.95 x AddOn)))
      EAD = 1.4 x (RC + multiplier x AddOn)

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from ..products.base import AssetClass, SACCRParameters
from ..riskfactors.taxonomy import RiskClass
from ..sensitivities.engine import SensitivityEngine, _currency_code, fx_convert
from .frtb_sa.parameters import COMMODITY_BUCKET

ALPHA = 1.4
_ASSET_CLASS = {AssetClass.INTEREST_RATE: "IR", AssetClass.FX: "FX", AssetClass.CROSS_CURRENCY: "FX",
                AssetClass.CREDIT: "CR", AssetClass.EQUITY: "EQ", AssetClass.COMMODITY: "CM"}
_PRIMARY = {"IR": RiskClass.INTEREST_RATE, "FX": RiskClass.FX, "CR": RiskClass.CREDIT,
            "EQ": RiskClass.EQUITY, "CM": RiskClass.COMMODITY}
# Commodity hedging sets (CRE52.69) from FRTB commodity buckets
_CM_HEDGING_SET = {1: "energy", 2: "energy", 3: "energy", 6: "energy", 5: "metals", 7: "metals",
                   8: "agricultural", 9: "agricultural", 10: "agricultural", 4: "other", 11: "other"}


@dataclass
class CSATerms:
    """Collateral terms of a netting set (amounts in the reporting currency)."""
    margined: bool = False
    collateral: float = 0.0          # net collateral held after haircuts (negative if posted)
    threshold: float = 0.0
    minimum_transfer_amount: float = 0.0
    nica: float = 0.0                # net independent collateral amount
    mpor_days: int = 10


@dataclass
class SACCRTrade:
    trade_id: str
    asset_class: str                 # IR, FX, CR, EQ, CM, OTHER
    hedging_key: str                 # currency / pair / entity / commodity
    signed_addon: float
    maturity: float
    mtm: float


@dataclass
class SACCRNettingSet:
    netting_set: str
    mtm: float
    collateral: float
    replacement_cost: float
    addon_by_class: Dict[str, float]
    addon: float
    multiplier: float
    ead: float
    trades: List[SACCRTrade] = field(default_factory=list)


def _primary_signs(trades: Sequence[Any], market_data: Any, ccy: Optional[str]) -> Dict[str, Dict[RiskClass, float]]:
    sens = SensitivityEngine().compute(list(trades), market_data, reporting_currency=ccy)
    out: Dict[str, Dict[RiskClass, float]] = {}
    for (tid, rc), v in sens.aggregate(("trade_id", "risk_class")).items():
        out.setdefault(tid, {})[rc] = v
    return out


def _hedging_key(trade: Any, cls: str) -> str:
    p = getattr(trade, "additional_params", {}) or {}
    if cls == "IR":
        return getattr(trade.currency, "value", str(trade.currency))
    if cls == "FX":
        if p.get("pair"):
            return p["pair"]
        base, quote = getattr(trade, "base_currency", None), getattr(trade, "quote_currency", None)
        return f"{getattr(base, 'value', base)}{getattr(quote, 'value', quote)}" if base else getattr(trade.currency, "value", "")
    if cls == "CR":
        return p.get("reference") or p.get("issuer") or p.get("pool") or trade.counterparty_id
    if cls == "EQ":
        return p.get("ticker", trade.trade_id)
    if cls == "CM":
        return str(p.get("commodity", getattr(getattr(trade, "terms", None), "commodity_type", "OTHER"))).upper()
    return trade.trade_id


def _aggregate(trades: List[SACCRTrade], index_names: Iterable[str]) -> Dict[str, float]:
    index_names = set(index_names)
    by_class: Dict[str, Dict[str, List[SACCRTrade]]] = {}
    for t in trades:
        by_class.setdefault(t.asset_class, {}).setdefault(t.hedging_key, []).append(t)
    out: Dict[str, float] = {}
    for cls, sets in by_class.items():
        if cls == "IR":
            total = 0.0
            for ts in sets.values():
                d = [0.0, 0.0, 0.0]
                for t in ts:
                    d[0 if t.maturity < 1 else 1 if t.maturity <= 5 else 2] += t.signed_addon
                total += math.sqrt(max(d[0] ** 2 + d[1] ** 2 + d[2] ** 2 + 1.4 * d[0] * d[1]
                                       + 1.4 * d[1] * d[2] + 0.6 * d[0] * d[2], 0.0))
            out[cls] = total
        elif cls == "FX":
            out[cls] = sum(abs(sum(t.signed_addon for t in ts)) for ts in sets.values())
        elif cls in ("CR", "EQ"):
            entities = {k: sum(t.signed_addon for t in ts) for k, ts in sets.items()}
            rho = {k: 0.8 if k in index_names else 0.5 for k in entities}
            sys = sum(rho[k] * a for k, a in entities.items())
            idio = sum((1 - rho[k] ** 2) * a * a for k, a in entities.items())
            out[cls] = math.sqrt(sys * sys + idio)
        elif cls == "CM":
            hedging: Dict[str, Dict[str, float]] = {}
            for k, ts in sets.items():
                hs = _CM_HEDGING_SET.get(COMMODITY_BUCKET.get(k, 11), "other")
                hedging.setdefault(hs, {})[k] = sum(t.signed_addon for t in ts)
            out[cls] = sum(math.sqrt((0.4 * sum(a.values())) ** 2 + 0.84 * sum(x * x for x in a.values()))
                           for a in hedging.values())
        else:
            out[cls] = sum(abs(t.signed_addon) for ts in sets.values() for t in ts)
    return out


def saccr_netting_sets(
    trades: Sequence[Any],
    market_data: Any,
    reporting_currency: Optional[str] = "USD",
    csa: Optional[Mapping[str, CSATerms]] = None,
    index_names: Iterable[str] = (),
) -> Dict[str, SACCRNettingSet]:
    """SA-CCR EAD per netting set (`trade.netting_set_id`, defaulting to the counterparty)."""
    trades = list(trades)
    csa = csa or {}
    signs = _primary_signs(trades, market_data, reporting_currency)
    groups: Dict[str, List[SACCRTrade]] = {}
    for t in trades:
        ns = getattr(t, "netting_set_id", None) or t.counterparty_id
        terms = csa.get(ns, CSATerms())
        sa = t.calculate_saccr(market_data)
        cls = _ASSET_CLASS.get(sa.asset_class, "OTHER")
        res = t.price(market_data)
        mtm = fx_convert(market_data, float(res.npv), _currency_code(res.currency), reporting_currency) \
            if reporting_currency else float(res.npv)
        primary = signs.get(t.trade_id, {}).get(_PRIMARY.get(cls), 0.0)
        sign = -1.0 if primary < 0 else 1.0
        maturity = t.get_remaining_maturity(market_data.valuation_date)
        addon = abs(sa.pfe_add_on)
        if terms.margined:                                   # replace unmargined MF by the margined MF
            mf_u = SACCRParameters.calculate_maturity_factor(maturity)
            addon *= (1.5 * math.sqrt(terms.mpor_days / 250.0)) / mf_u if mf_u > 0 else 1.0
        groups.setdefault(ns, []).append(SACCRTrade(t.trade_id, cls, _hedging_key(t, cls), sign * addon, maturity, mtm))

    out = {}
    for ns, ts in groups.items():
        terms = csa.get(ns, CSATerms())
        v, c = sum(t.mtm for t in ts), terms.collateral
        rc = max(v - c, terms.threshold + terms.minimum_transfer_amount - terms.nica, 0.0) if terms.margined \
            else max(v - c, 0.0)
        by_class = _aggregate(ts, index_names)
        addon = sum(by_class.values())
        mult = min(1.0, 0.05 + 0.95 * math.exp((v - c) / (2 * 0.95 * addon))) if addon > 0 else 1.0
        out[ns] = SACCRNettingSet(ns, v, c, rc, by_class, addon, mult, ALPHA * (rc + mult * addon), ts)
    return out


__all__ = ["CSATerms", "SACCRTrade", "SACCRNettingSet", "saccr_netting_sets"]
