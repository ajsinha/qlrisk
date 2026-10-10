"""
QLRisk - Unified Risk Engine
============================

Every risk, one engine: one call produces PVs, sensitivities, VaR / ES,
stressed VaR, stress tests, backtests, FRTB SA capital and counterparty
exposure for a book, rolled up a reporting hierarchy and checked against
limits.

    from qlrisk.engine import RiskEngine
    from qlrisk.reporting import Hierarchy, RiskLimit

    engine = RiskEngine(reporting_currency="USD")
    report = engine.run(trades, md, history, hierarchy=Hierarchy(paths),
                        limits=[RiskLimit("Firm VaR", "var.1d", 2e6)])
    print(report)

The existing CCREngine and MarketRiskEngine remain available and unchanged.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

from ..pnl.revaluation import _pv
from ..reporting.hierarchy import ROOT, Hierarchy
from ..reporting.limits_monitor import RiskLimit, check_limits
from ..reporting.report import RiskReport
from ..riskfactors.timeseries import RiskFactorTimeSeries
from ..scenarios.generators import historical_scenarios
from ..sensitivities.measures import SensitivityMeasure
from .market_risk_engine import MarketRiskEngine

ALL_MEASURES = ("PV", "SENSITIVITIES", "VAR", "ES", "PARAMETRIC_VAR", "SVAR", "STRESS", "BACKTEST",
                "FRTB_SA", "EXPOSURE")
DEFAULT_MEASURES = ("PV", "SENSITIVITIES", "VAR", "ES", "SVAR", "STRESS", "FRTB_SA", "EXPOSURE")
HISTORY_MEASURES = {"VAR", "ES", "PARAMETRIC_VAR", "SVAR", "BACKTEST"}

_CONFIG_KEYS = {
    "marketrisk.reporting_currency": ("reporting_currency", str),
    "marketrisk.confidence": ("confidence", float),
    "marketrisk.es_confidence": ("es_confidence", float),
    "marketrisk.lookback": ("lookback", int),
    "marketrisk.horizon_days": ("horizon_days", int),
    "marketrisk.stress_window": ("stress_window", int),
    "engine.max_workers": ("max_workers", int),
}


class RiskEngine:
    """
    Args:
        reporting_currency: Currency of every reported number
        confidence / es_confidence: VaR and ES confidence levels
        lookback: Historical-simulation window (days)
        horizon_days: Long holding period for VaR and SVaR (sqrt-scaled from 1 day)
        stress_window: Stressed-period window length (days)
        max_workers: Threads for revaluation and sensitivities
    """

    def __init__(self, reporting_currency: str = "USD", confidence: float = 0.99, es_confidence: float = 0.975,
                 lookback: int = 250, horizon_days: int = 10, stress_window: int = 250, max_workers: int = 1):
        self.reporting_currency = reporting_currency
        self.confidence, self.es_confidence = confidence, es_confidence
        self.lookback, self.horizon_days, self.stress_window = lookback, horizon_days, stress_window
        self.market = MarketRiskEngine(reporting_currency, max_workers)

    def __enter__(self) -> "RiskEngine":
        return self

    def __exit__(self, *exc) -> None:
        return None

    @classmethod
    def from_config(cls, path: Optional[str] = None, **overrides) -> "RiskEngine":
        """Build from a .properties file (default: the packaged config/application.properties)."""
        path = path or str(Path(__file__).resolve().parents[1] / "config" / "application.properties")
        kwargs: Dict[str, Any] = {}
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = (s.strip() for s in line.split("=", 1))
                if k in _CONFIG_KEYS:
                    name, cast = _CONFIG_KEYS[k]
                    kwargs[name] = cast(v)
        kwargs.update(overrides)
        return cls(**kwargs)

    def run(
        self,
        trades: Sequence[Any],
        market_data: Any,
        history: Optional[RiskFactorTimeSeries] = None,
        measures: Iterable[str] = DEFAULT_MEASURES,
        hierarchy: Optional[Hierarchy] = None,
        limits: Optional[Sequence[RiskLimit]] = None,
        frtb: Optional[Mapping[str, Any]] = None,
    ) -> RiskReport:
        """
        Run the requested measures and return a RiskReport.

        Args:
            trades: The book
            market_data: Today's products.base.MarketData
            history: Factor history (required for VAR, ES, PARAMETRIC_VAR, SVAR, BACKTEST)
            measures: Subset of ALL_MEASURES
            hierarchy: Reporting tree; defaults to one node per counterparty
            limits: Limits to check; results in report.results['limits']
            frtb: Keyword arguments for frtb_sa_capital (bucket maps, ratings, vol underlyings)
        """
        trades = list(trades)
        wanted = [m.upper() for m in measures]
        unknown = set(wanted) - set(ALL_MEASURES)
        if unknown:
            raise ValueError(f"Unknown measures {sorted(unknown)}; choose from {ALL_MEASURES}")
        report = RiskReport(market_data.valuation_date, self.reporting_currency)
        if history is None and HISTORY_MEASURES & set(wanted):
            report.notes.append(f"No history supplied: skipped {sorted(HISTORY_MEASURES & set(wanted))}")
            wanted = [m for m in wanted if m not in HISTORY_MEASURES]
        tree = hierarchy or Hierarchy({t.trade_id: (t.counterparty_id,) for t in trades}, ("counterparty",))
        ids = [t.trade_id for t in trades]
        nodes = {n: {} for n in tree.nodes(ids)}
        report.by_node = nodes
        mre, conf, esc = self.market, self.confidence, self.es_confidence

        def add_additive(metric: str, per_trade: Mapping[str, float]) -> None:
            for node, value in tree.sum_by_node(per_trade).items():
                nodes.setdefault(node, {})[metric] = value

        if "PV" in wanted:
            pv = {t.trade_id: _pv(t, market_data, self.reporting_currency) for t in trades}
            report.metrics["pv.total"] = sum(pv.values())
            add_additive("pv", pv)

        sens = None
        if "SENSITIVITIES" in wanted or "PARAMETRIC_VAR" in wanted:
            sens = mre.sensitivities(trades, market_data)
            report.results["sensitivities"] = sens
            for (rc, m), v in sens.aggregate(("risk_class", "measure")).items():
                report.metrics[f"{m.value}.{rc.value}"] = v
            for m in (SensitivityMeasure.DV01, SensitivityMeasure.CS01, SensitivityMeasure.VEGA):
                per_trade = {t: 0.0 for t in ids}
                for (t, mm), v in sens.aggregate(("trade_id", "measure")).items():
                    if mm is m:
                        per_trade[t] = v
                add_additive(m.value, per_trade)
            if sens.errors:
                report.notes.append(f"{len(sens.errors)} sensitivity pricing errors (see results['sensitivities'])")

        if "VAR" in wanted or "ES" in wanted:
            pnl = mre.scenario_pnl(trades, market_data, historical_scenarios(history, lookback=self.lookback))
            report.results["pnl"] = pnl
            if "VAR" in wanted:
                var = pnl.var(conf)
                report.results["var"] = var
                report.metrics["var.1d"] = var.value
                report.metrics[f"var.{self.horizon_days}d"] = var.value * self.horizon_days ** 0.5
                for node, res in tree.measure_by_node(pnl, conf, "var").items():
                    nodes[node]["var.1d"] = res.value
            if "ES" in wanted:
                es = pnl.es(esc)
                report.results["es"] = es
                report.metrics["es.1d"] = es.value
                for node, res in tree.measure_by_node(pnl, esc, "es").items():
                    nodes[node]["es.1d"] = res.value

        if "PARAMETRIC_VAR" in wanted:
            pvar = mre.parametric_var(trades, market_data, history, conf, lookback=self.lookback, sensitivities=sens)
            report.results["parametric_var"] = pvar
            report.metrics["parametric_var.1d"] = pvar.value

        if "SVAR" in wanted:
            svar = mre.stressed_var(trades, market_data, history, self.stress_window, conf, self.horizon_days)
            report.results["svar"] = svar
            report.metrics[f"svar.{self.horizon_days}d"] = svar.value

        if "STRESS" in wanted:
            stress = mre.stress_test(trades, market_data)
            report.results["stress"] = stress
            worst = min(stress, key=stress.get)
            report.metrics["stress.worst"] = stress[worst]
            report.notes.append(f"Worst stress scenario: {worst}")

        if "BACKTEST" in wanted:
            test_days = min(250, len(history) - self.lookback - 2)
            bt = mre.backtest(trades, market_data, history, test_days=test_days, lookback=self.lookback,
                              confidence=conf, es_confidence=esc)
            report.results["backtest"] = bt
            report.metrics["backtest.exceptions"] = bt["var"].exceptions
            report.notes.append(f"Backtest zone {bt['var'].zone}, ES zone {bt['es'].zone}, PLA zone {bt['pla'].zone}")

        if "FRTB_SA" in wanted:
            from ..regulatory.frtb_sa import frtb_sa_capital
            sa = frtb_sa_capital(trades, market_data, self.reporting_currency, **dict(frtb or {}))
            report.results["frtb_sa"] = sa
            for k, v in sa.summary().items():
                report.metrics[f"frtb_sa.{k.lower()}"] = v
            if sa.sbm.skipped_factors:
                report.notes.append(f"FRTB: unmapped factors {sa.sbm.skipped_factors}")

        if "EXPOSURE" in wanted:
            pfe, ead = {}, {}
            for t in trades:
                try:
                    pfe[t.trade_id] = t.calculate_ccr_exposure(market_data, num_scenarios=1000).peak_exposure
                    ead[t.trade_id] = t.calculate_saccr(market_data).ead
                except Exception as exc:
                    report.notes.append(f"Exposure failed for {t.trade_id}: {type(exc).__name__}: {exc}")
            report.metrics["exposure.peak_pfe_sum"] = sum(pfe.values())
            report.metrics["exposure.saccr_ead_sum"] = sum(ead.values())
            add_additive("peak_pfe", pfe)
            add_additive("saccr_ead", ead)
            report.notes.append("Exposure: trade-level PFE / SA-CCR EAD summed per node (no netting-set aggregation)")

        for metric, value in report.metrics.items():
            nodes[ROOT].setdefault(metric, value)
        if limits:
            report.results["limits"] = check_limits(report, limits)
        return report


__all__ = ["RiskEngine", "ALL_MEASURES", "DEFAULT_MEASURES"]
