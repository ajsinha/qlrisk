"""
QLRisk - Market Risk Engine
===========================

One entry point for market-risk measures on a list of trades:

    from qlrisk.engine import MarketRiskEngine
    from qlrisk.scenarios import historical_scenarios

    with MarketRiskEngine(reporting_currency="USD") as mre:
        scen = historical_scenarios(history, lookback=500)
        var = mre.var(trades, md, scen, confidence=0.99)           # full revaluation
        es  = mre.es(trades, md, scen, confidence=0.975)
        pvar = mre.parametric_var(trades, md, history)             # delta-normal
        svar = mre.stressed_var(trades, md, history, window=250, horizon_days=10)

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Any, Dict, Optional, Sequence

import numpy as np
from scipy.stats import norm

from ..calculator.python.var_calculators import parametric_es, parametric_var
from ..models.risk_measure import RiskMeasureResult
from ..pnl.matrix import PnLMatrix
from ..pnl.revaluation import _pv as full_revaluation_pv, full_revaluation
from ..pnl.taylor import taylor_pnl
from ..riskfactors.mapping import get_factor_value
from ..riskfactors.shocks import ShockType
from ..riskfactors.timeseries import RiskFactorTimeSeries
from ..scenarios.generators import covariance, historical_scenarios
from ..scenarios.scenario_set import ScenarioSet
from ..scenarios.stressed_period import find_stress_window
from ..sensitivities.engine import SensitivityEngine
from ..sensitivities.results import SensitivityResult

FULL = "full"
TAYLOR = "taylor"


class MarketRiskEngine:
    """
    Market-risk calculations over a list of trades.

    Args:
        reporting_currency: Currency for all P&L / risk (recommended for multi-currency books)
        max_workers: Threads for full revaluation and sensitivities
        sensitivity_engine: Custom SensitivityEngine (bumps, method)
    """

    def __init__(self, reporting_currency: Optional[str] = None, max_workers: int = 1,
                 sensitivity_engine: Optional[SensitivityEngine] = None):
        self.reporting_currency = reporting_currency
        self.max_workers = max_workers
        self.sensitivity_engine = sensitivity_engine or SensitivityEngine(max_workers=max_workers)

    def __enter__(self) -> "MarketRiskEngine":
        return self

    def __exit__(self, *exc) -> None:
        return None

    # ---------------------------------------------------------------- building blocks

    def sensitivities(self, trades: Sequence[Any], market_data: Any, **kwargs) -> SensitivityResult:
        """Bump-and-reprice sensitivities in the reporting currency."""
        kwargs.setdefault("reporting_currency", self.reporting_currency)
        return self.sensitivity_engine.compute(list(trades), market_data, **kwargs)

    def scenario_pnl(self, trades: Sequence[Any], market_data: Any, scenarios: ScenarioSet,
                     method: str = FULL, order: int = 2,
                     sensitivities: Optional[SensitivityResult] = None) -> PnLMatrix:
        """P&L of every trade in every scenario, by full revaluation or Taylor expansion."""
        if method == FULL:
            return full_revaluation(trades, market_data, scenarios, self.reporting_currency, self.max_workers)
        if method == TAYLOR:
            sens = sensitivities or self.sensitivities(trades, market_data)
            return taylor_pnl(sens, market_data, scenarios, order)
        raise ValueError(f"method must be '{FULL}' or '{TAYLOR}'")

    # ---------------------------------------------------------------- VaR / ES

    def var(self, trades: Sequence[Any], market_data: Any, scenarios: ScenarioSet,
            confidence: float = 0.99, method: str = FULL) -> RiskMeasureResult:
        """Scenario VaR (historical / filtered / age-weighted / Monte Carlo, per the scenario set)."""
        return self.scenario_pnl(trades, market_data, scenarios, method).var(confidence)

    def es(self, trades: Sequence[Any], market_data: Any, scenarios: ScenarioSet,
           confidence: float = 0.975, method: str = FULL) -> RiskMeasureResult:
        """Scenario Expected Shortfall."""
        return self.scenario_pnl(trades, market_data, scenarios, method).es(confidence)

    def parametric_var(self, trades: Sequence[Any], market_data: Any, history: RiskFactorTimeSeries,
                       confidence: float = 0.99, horizon_days: int = 1, lookback: Optional[int] = None,
                       ewma_lambda: Optional[float] = None, measure: str = "var",
                       sensitivities: Optional[SensitivityResult] = None) -> RiskMeasureResult:
        """
        Delta-normal VaR (or ES) from sensitivities and the factor-return covariance.

        Exposure to factor j: e_j = dPV/dx_j (absolute-return factors) or dPV/dx_j * x_j
        (relative / log). sigma_P = sqrt(e' C e * h). Component contributions per trade are
        Euler allocations: z * (e_trade' C e) / sigma_P * h.
        """
        sens = sensitivities or self.sensitivities(trades, market_data)
        scen = historical_scenarios(history, lookback=lookback).restrict_to(market_data)
        cov = covariance(scen.returns, ewma_lambda)
        col = {k: j for j, k in enumerate(scen.factors)}
        trade_ids = list(sens.base_pv)
        row = {t: i for i, t in enumerate(trade_ids)}
        expo = np.zeros((len(trade_ids), len(scen.factors)))
        for rec in sens.records:
            if rec.factor in col and rec.derivative is not None and rec.trade_id in row:
                j = col[rec.factor]
                scale = 1.0 if scen.return_types[j] is ShockType.ABSOLUTE else get_factor_value(market_data, rec.factor)
                expo[row[rec.trade_id], j] += rec.derivative * scale
        total = expo.sum(axis=0)
        sigma = float(np.sqrt(max(total @ cov @ total, 0.0) * horizon_days))
        if measure == "var":
            value, mult = parametric_var(0.0, sigma, confidence), -norm.ppf(1 - confidence)
        else:
            alpha = 1 - confidence
            value, mult = parametric_es(0.0, sigma, confidence), norm.pdf(norm.ppf(alpha)) / alpha
        contrib = {}
        if sigma > 0:
            marginal = cov @ total * horizon_days / sigma
            contrib = {t: float(mult * expo[i] @ marginal) for i, t in enumerate(trade_ids)}
        return RiskMeasureResult("VaR" if measure == "var" else "ES", value, confidence, horizon_days,
                                 "parametric_delta_normal", len(scen), sens.currency, contrib,
                                 metadata={"sigma": sigma, "ewma_lambda": ewma_lambda, "lookback": lookback})

    def stressed_var(self, trades: Sequence[Any], market_data: Any, history: RiskFactorTimeSeries,
                     window: int = 250, confidence: float = 0.99, horizon_days: int = 10,
                     search_method: str = TAYLOR, method: str = FULL,
                     measure: str = "var") -> RiskMeasureResult:
        """
        Stressed VaR (or stressed ES): find the `window`-day period of 1-day returns that maximises
        the portfolio's risk (searched with `search_method`, Taylor by default for speed), then
        measure it on that window with `method`, scaled by sqrt(horizon_days).
        """
        all_days = historical_scenarios(history)
        search = self.scenario_pnl(trades, market_data, all_days, search_method)
        win = find_stress_window(search.portfolio, search.labels, window, confidence, measure)
        stressed = historical_scenarios(history, horizon=horizon_days, sqrt_scaling=True)
        stressed = stressed.subset(range(win.start_index, win.end_index))
        stressed.method = "stressed_historical"
        pnl = self.scenario_pnl(trades, market_data, stressed, method)
        result = pnl.var(confidence) if measure == "var" else pnl.es(confidence)
        result.measure = "SVaR" if measure == "var" else "SES"
        result.metadata.update({"window_start": win.start, "window_end": win.end, "window": window,
                                "search_method": search_method, "scaling": f"sqrt({horizon_days})"})
        return result

    # ---------------------------------------------------------------- validation & stress
    
    def backtest(self, trades: Sequence[Any], market_data: Any, history: RiskFactorTimeSeries,
                 test_days: int = 250, lookback: int = 250, confidence: float = 0.99,
                 es_confidence: float = 0.975) -> Dict[str, Any]:
        """
        Backtest historical VaR / ES of the current (static) portfolio over the last `test_days`.
        
        For each test day t: VaR_t and ES_t from the `lookback` 1-day returns before t (Taylor P&L
        with today's sensitivities, i.e. the risk-theoretical model); realised hypothetical P&L =
        full revaluation from the market of day t-1 to day t (history.market_data_at).
        Returns VaR backtest, ES backtest, PLA test (HPL vs RTPL) and the daily series.
        """
        from ..backtesting import backtest_es, backtest_var
        from ..calculator.python.var_calculators import expected_shortfall, value_at_risk
        from ..pnl.attribution import pla_test
        
        trades = list(trades)
        n_ret = len(history) - 1
        if test_days + lookback > n_ret:
            raise ValueError(f"history too short: need {test_days + lookback + 1} dates, have {len(history)}")
        rtpl_all = self.scenario_pnl(trades, market_data, historical_scenarios(history), TAYLOR).portfolio
        dates = history.dates
        var_f, es_f, hpl, rtpl, labels = [], [], [], [], []
        pv = lambda md: sum(full_revaluation_pv(t, md, self.reporting_currency) for t in trades)
        prev_md = history.market_data_at(dates[n_ret - test_days], market_data)
        prev_pv = pv(prev_md)
        for i in range(n_ret - test_days, n_ret):          # return index i ends at dates[i + 1]
            window = rtpl_all[i - lookback:i]
            var_f.append(value_at_risk(window, confidence))
            es_f.append(expected_shortfall(window, es_confidence))
            md_t = history.market_data_at(dates[i + 1], market_data)
            pv_t = pv(md_t)
            hpl.append(pv_t - prev_pv)
            rtpl.append(rtpl_all[i])
            labels.append(dates[i + 1])
            prev_pv = pv_t
        es_var = [value_at_risk(rtpl_all[i - lookback:i], es_confidence) for i in range(n_ret - test_days, n_ret)]
        return {
            "var": backtest_var(hpl, var_f, confidence, labels),
            "es": backtest_es(hpl, es_var, es_f, es_confidence),
            "pla": pla_test(hpl, rtpl),
            "series": {"dates": labels, "hpl": hpl, "rtpl": rtpl, "var": var_f, "es": es_f},
        }
    
    def stress_test(self, trades: Sequence[Any], market_data: Any,
                    scenarios: Optional[ScenarioSet] = None) -> Dict[Any, float]:
        """Portfolio P&L under each scenario (default: the historical stress library)."""
        from ..scenarios.stress_library import historical_stress_scenarios
        scen = scenarios or historical_stress_scenarios(market_data)
        pnl = self.scenario_pnl(trades, market_data, scen)
        return dict(zip(pnl.labels, pnl.portfolio.tolist()))
    
    def reverse_stress(self, trades: Sequence[Any], market_data: Any, history: RiskFactorTimeSeries,
                       loss: float, lookback: int = 250):
        """Most plausible scenario producing `loss`; see scenarios.reverse_stress_test."""
        from ..scenarios.reverse_stress import reverse_stress_test
        return reverse_stress_test(trades, market_data, history, loss, lookback, self.reporting_currency)
    
    def explain(self, trades: Sequence[Any], md_start: Any, md_end: Any):
        """P&L explain between two snapshots; see pnl.explain_pnl."""
        from ..pnl.attribution import explain_pnl
        return explain_pnl(list(trades), md_start, md_end, reporting_currency=self.reporting_currency)
    
    # ---------------------------------------------------------------- summary

    def summary(self, trades: Sequence[Any], market_data: Any, history: RiskFactorTimeSeries,
                lookback: int = 250, stress_window: int = 250) -> Dict[str, RiskMeasureResult]:
        """Standard daily pack: 1d/10d historical VaR 99%, ES 97.5%, parametric VaR, stressed VaR."""
        one_day = historical_scenarios(history, lookback=lookback)
        pnl = self.scenario_pnl(trades, market_data, one_day)
        ten_day = historical_scenarios(history, lookback=lookback, horizon=10, sqrt_scaling=True)
        return {
            "var_1d_99": pnl.var(0.99),
            "es_1d_975": pnl.es(0.975),
            "var_10d_99": self.var(trades, market_data, ten_day, 0.99),
            "parametric_var_1d_99": self.parametric_var(trades, market_data, history, lookback=lookback),
            "stressed_var_10d_99": self.stressed_var(trades, market_data, history, window=stress_window),
        }


__all__ = ["MarketRiskEngine", "FULL", "TAYLOR"]
