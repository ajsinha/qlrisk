"""
QLRisk - P&L Explain and FRTB P&L Attribution Test
==================================================

explain_pnl: splits the change in value between two market-data snapshots into
    theta (time roll at unchanged market) + sum over factors of (delta dx + 1/2 gamma dx^2)
    + unexplained (actual full-revaluation P&L minus everything explained).

pla_test: FRTB MAR32 P&L attribution test comparing hypothetical P&L (HPL)
with risk-theoretical P&L (RTPL): Spearman correlation and Kolmogorov-Smirnov
distance. Green: rho > 0.80 and KS < 0.09; red: rho < 0.70 or KS > 0.12;
amber otherwise.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence

import numpy as np
from scipy.stats import ks_2samp, spearmanr

from ..riskfactors.mapping import enumerate_risk_factors, get_factor_value
from ..riskfactors.taxonomy import RiskFactorKey
from ..sensitivities.engine import SensitivityEngine, _currency_code, fx_convert
from ..sensitivities.results import SensitivityResult


@dataclass
class TradeExplain:
    trade_id: str
    actual: float
    theta: float
    by_risk_class: Dict[str, float]
    by_factor: Dict[RiskFactorKey, float] = field(repr=False)
    
    @property
    def explained(self) -> float:
        return self.theta + sum(self.by_risk_class.values())
    
    @property
    def unexplained(self) -> float:
        return self.actual - self.explained


@dataclass
class PnLExplain:
    trades: Dict[str, TradeExplain]
    currency: Optional[str] = None
    
    def total(self) -> Dict[str, float]:
        out = {"actual": 0.0, "theta": 0.0, "unexplained": 0.0}
        for t in self.trades.values():
            out["actual"] += t.actual
            out["theta"] += t.theta
            out["unexplained"] += t.unexplained
            for rc, v in t.by_risk_class.items():
                out[rc] = out.get(rc, 0.0) + v
        return out


def explain_pnl(
    trades: Sequence[Any],
    md_start: Any,
    md_end: Any,
    sensitivities: Optional[SensitivityResult] = None,
    reporting_currency: Optional[str] = None,
) -> PnLExplain:
    """Explain P&L from md_start to md_end (sensitivities taken at md_start)."""
    sens = sensitivities or SensitivityEngine().compute(list(trades), md_start, reporting_currency=reporting_currency)
    end_factors = set(enumerate_risk_factors(md_end))
    rolled = copy.copy(md_start)
    rolled.valuation_date = md_end.valuation_date
    
    def pv(trade, md):
        res = trade.price(md)
        return fx_convert(md, float(res.npv), _currency_code(res.currency), reporting_currency) \
            if reporting_currency else float(res.npv)
    
    out = {}
    for trade in trades:
        start = pv(trade, md_start)
        by_factor: Dict[RiskFactorKey, float] = {}
        for rec in sens.filter(trade_id=trade.trade_id):
            if rec.factor is None or rec.derivative is None or rec.factor not in end_factors:
                continue
            dx = get_factor_value(md_end, rec.factor) - get_factor_value(md_start, rec.factor)
            contrib = rec.derivative * dx
            if rec.gamma is not None:
                level = get_factor_value(md_start, rec.factor)
                step = rec.bump_size * level if rec.bump_type.value == "relative" else rec.bump_size
                contrib += 0.5 * rec.gamma / step ** 2 * dx * dx
            by_factor[rec.factor] = by_factor.get(rec.factor, 0.0) + contrib
        by_class: Dict[str, float] = {}
        for k, v in by_factor.items():
            by_class[k.risk_class.value] = by_class.get(k.risk_class.value, 0.0) + v
        out[trade.trade_id] = TradeExplain(trade.trade_id, pv(trade, md_end) - start, pv(trade, rolled) - start,
                                           by_class, by_factor)
    return PnLExplain(out, reporting_currency)


@dataclass
class PLAResult:
    spearman: float
    ks_statistic: float
    zone: str
    n: int


def pla_test(hpl: Sequence[float], rtpl: Sequence[float]) -> PLAResult:
    """FRTB P&L attribution test on daily hypothetical vs risk-theoretical P&L."""
    h, r = np.asarray(hpl, dtype=float), np.asarray(rtpl, dtype=float)
    if h.shape != r.shape or h.ndim != 1 or h.size < 10:
        raise ValueError("hpl and rtpl must be equal-length 1-D arrays with at least 10 observations")
    rho = float(spearmanr(h, r)[0])
    ks = float(ks_2samp(h, r).statistic)
    if rho > 0.80 and ks < 0.09:
        zone = "green"
    elif rho < 0.70 or ks > 0.12:
        zone = "red"
    else:
        zone = "amber"
    return PLAResult(rho, ks, zone, h.size)


__all__ = ["explain_pnl", "PnLExplain", "TradeExplain", "pla_test", "PLAResult"]
