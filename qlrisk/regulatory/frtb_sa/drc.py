"""
QLRisk - FRTB SA Default Risk Charge, non-securitisations (MAR22)
================================================================

    JTD_long  = max(LGD * notional + P&L, 0)      JTD_short = min(LGD * notional + P&L, 0)
    P&L = market value - notional; JTD scaled by min(max(maturity, 0.25), 1)
    Net JTD per obligor; per bucket (corporates, sovereigns, local governments):
    HBR   = sum(net long) / (sum(net long) + sum(|net short|))
    DRC_b = max(sum(RW * JTD_long) - HBR * sum(RW * |JTD_short|), 0);  DRC = sum_b DRC_b

Simplification: long and short JTDs of the same obligor are netted regardless of seniority.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence

from . import parameters as p


@dataclass
class DRCPosition:
    """A default exposure. Long credit risk: notional > 0; short (e.g. bought protection): notional < 0."""
    obligor: str
    rating: str
    notional: float
    market_value: float
    maturity: float
    seniority: str = "SENIOR"
    bucket: str = "corporates"
    trade_id: str = ""
    
    @property
    def jtd(self) -> float:
        lgd = p.DRC_LGD[self.seniority]
        raw = lgd * self.notional + (self.market_value - self.notional)
        jtd = max(raw, 0.0) if self.notional >= 0 else min(raw, 0.0)
        return jtd * min(max(self.maturity, 0.25), 1.0)


@dataclass
class DRCResult:
    total: float
    by_bucket: Dict[str, float]
    net_jtd: Dict[str, float]
    hbr: Dict[str, float] = field(default_factory=dict)


def drc_charge(positions: Sequence[DRCPosition]) -> DRCResult:
    net: Dict[str, float] = {}
    meta: Dict[str, DRCPosition] = {}
    for pos in positions:
        net[pos.obligor] = net.get(pos.obligor, 0.0) + pos.jtd
        meta.setdefault(pos.obligor, pos)
    buckets: Dict[str, List[str]] = {}
    for ob in net:
        buckets.setdefault(meta[ob].bucket, []).append(ob)
    by_bucket, hbr = {}, {}
    for b, obligors in buckets.items():
        longs = [net[o] for o in obligors if net[o] > 0]
        shorts = [net[o] for o in obligors if net[o] < 0]
        h = sum(longs) / (sum(longs) + abs(sum(shorts))) if (longs or shorts) and (sum(longs) + abs(sum(shorts))) else 0.0
        rw = lambda o: p.DRC_RW[meta[o].rating.upper()]
        weighted_long = sum(rw(o) * net[o] for o in obligors if net[o] > 0)
        weighted_short = sum(rw(o) * abs(net[o]) for o in obligors if net[o] < 0)
        by_bucket[b] = max(weighted_long - h * weighted_short, 0.0)
        hbr[b] = h
    return DRCResult(sum(by_bucket.values()), by_bucket, net, hbr)


_BOND_TERMS = ("issuer",)


def drc_positions_from_trades(
    trades: Sequence[Any],
    market_data: Any,
    ratings: Optional[Mapping[str, str]] = None,
    seniority: Optional[Mapping[str, str]] = None,
    buckets: Optional[Mapping[str, str]] = None,
) -> List[DRCPosition]:
    """
    Default exposures implied by trades:
      - bonds / FRNs / CLNs with an `issuer` term: long, notional = trade notional, MV = PV
      - CDS / CDS index with a `reference` term: bought protection -> short, sold -> long (LGD x notional)
      - cash equities with a `ticker` term: long, EQUITY seniority, notional = MV
    Ratings default to UNRATED, seniority to SENIOR, bucket to corporates.
    """
    ratings, seniority, buckets = ratings or {}, seniority or {}, buckets or {}
    out = []
    for t in trades:
        terms = getattr(t, "additional_params", {}) or {}
        mat = max((t.maturity_date - market_data.valuation_date).days / 365.25, 0.0)
        name = terms.get("issuer") or terms.get("reference")
        if terms.get("issuer"):
            mv = t.price(market_data).npv
            sign = 1.0 if terms.get("is_long", True) else -1.0
            out.append(DRCPosition(name, ratings.get(name, "UNRATED"), sign * t.notional, mv, mat,
                                   seniority.get(name, "SENIOR"), buckets.get(name, "corporates"), t.trade_id))
        elif terms.get("reference"):
            sign = -1.0 if terms.get("is_buyer", True) else 1.0
            n = sign * t.notional
            out.append(DRCPosition(name, ratings.get(name, "UNRATED"), n, n, mat,
                                   seniority.get(name, "SENIOR"), buckets.get(name, "corporates"), t.trade_id))
        elif terms.get("ticker") and type(t).__name__ in ("CommonStock", "PreferredStock", "ADR", "GDR"):
            mv = t.price(market_data).npv
            out.append(DRCPosition(terms["ticker"], ratings.get(terms["ticker"], "UNRATED"), mv, mv, 1.0,
                                   "EQUITY", buckets.get(terms["ticker"], "corporates"), t.trade_id))
    return out


__all__ = ["DRCPosition", "DRCResult", "drc_charge", "drc_positions_from_trades"]
