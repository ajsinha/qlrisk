"""Tests for the unified RiskEngine, reporting hierarchy, reports, limits, wrong-way risk and CLI demos."""

import json
from datetime import date

import numpy as np
import pytest

import qlrisk.products.python as P
from qlrisk.data import MarketHistoryGenerator, create_sample_market_data
from qlrisk.engine import ALL_MEASURES, RiskEngine
from qlrisk.models.limit import LimitStatus
from qlrisk.pnl import PnLMatrix
from qlrisk.products.base import Currency
from qlrisk.reporting import Hierarchy, RiskLimit, RiskReport, breaches, check_limits
from qlrisk.scenarios import wrong_way_exposure

from conftest import VALUATION_DATE


@pytest.fixture(scope="module")
def setup():
    md = create_sample_market_data(VALUATION_DATE)
    d0 = md.valuation_date
    book = [
        P.InterestRateSwap("IRS", d0, d0, date(2036, 10, 9), 25e6, Currency.USD, "BANK-A", fixed_rate=0.043),
        P.CorporateBond("BOND", d0, d0, date(2031, 10, 9), 10e6, Currency.USD, "ACME", coupon=0.05, issuer="ACME"),
        P.EquityOption("PUT", d0, d0, date(2027, 4, 9), 5e6, Currency.USD, "BANK-A", ticker="SPX", strike=5000.0,
                       is_call=False),
    ]
    hist = MarketHistoryGenerator(seed=7).generate(md, num_days=600, stress_start=200, stress_days=50)
    tree = Hierarchy({"IRS": ("Firm", "Rates"), "BOND": ("Firm", "Credit"), "PUT": ("Firm", "Equity")})
    return md, book, hist, tree


def test_hierarchy_rollups():
    tree = Hierarchy({"A": ("E", "D1"), "B": ("E", "D1"), "C": ("E", "D2")})
    assert tree.nodes(["A", "B", "C"]) == ["ALL", "E", "E/D1", "E/D2"]
    assert tree.sum_by_node({"A": 1.0, "B": 2.0, "C": 4.0}) == {"ALL": 7.0, "E": 7.0, "E/D1": 3.0, "E/D2": 4.0}
    rng = np.random.default_rng(0)
    pnl = PnLMatrix(["A", "B", "C"], list(range(400)), rng.standard_normal((3, 400)))
    by = tree.var_by_node(pnl)
    assert by["E/D1"].value == pytest.approx(pnl.subset(["A", "B"]).var().value)
    assert all(v >= -1e-9 for v in tree.diversification(pnl).values())


def test_report_export_and_limits(tmp_path):
    rep = RiskReport(VALUATION_DATE, "USD", {"var.1d": 900.0}, {"ALL": {"var.1d": 900.0}, "Firm/Rates": {"var.1d": 950.0}})
    assert rep.value("var.1d", "Firm/Rates") == 950.0 and rep.value("var.1d") == 900.0
    assert json.loads(rep.to_json())["metrics"]["var.1d"] == 900.0
    rep.to_csv(str(tmp_path / "r.csv"))
    assert (tmp_path / "r.csv").read_text().count("\n") == 3
    checks = check_limits(rep, [RiskLimit("a", "var.1d", 2000), RiskLimit("b", "var.1d", 1100),
                                RiskLimit("c", "var.1d", 1000, node="Firm/Rates"), RiskLimit("d", "var.1d", 900, node="Firm/Rates"),
                                RiskLimit("e", "missing", 1)])
    assert [c.status for c in checks] == [LimitStatus.GREEN, LimitStatus.AMBER, LimitStatus.RED, LimitStatus.BREACH, None]
    assert [c.name for c in breaches(checks)] == ["d"]


def test_risk_engine_full_run(setup):
    md, book, hist, tree = setup
    engine = RiskEngine(reporting_currency="USD")
    rep = engine.run(book, md, hist, measures=ALL_MEASURES, hierarchy=tree,
                     frtb={"credit_buckets": {"ACME": 4}, "equity_buckets": {"SPX": 12}, "ratings": {"ACME": "BBB"}},
                     limits=[RiskLimit("VaR", "var.1d", 1e9)])
    m = rep.metrics
    for k in ("pv.total", "var.1d", "var.10d", "es.1d", "parametric_var.1d", "svar.10d", "stress.worst",
              "backtest.exceptions", "frtb_sa.total", "exposure.saccr_ead_netted", "dv01.IR"):
        assert k in m, k
    assert m["var.10d"] == pytest.approx(m["var.1d"] * np.sqrt(10))
    desks = sum(rep.by_node[n]["var.1d"] for n in ("Firm/Rates", "Firm/Credit", "Firm/Equity"))
    assert desks >= rep.by_node["Firm"]["var.1d"] == pytest.approx(m["var.1d"])        # diversification
    assert rep.by_node["ALL"]["pv"] == pytest.approx(m["pv.total"])
    assert sum(rep.by_node[n]["dv01"] for n in ("Firm/Rates", "Firm/Credit", "Firm/Equity")) == pytest.approx(
        rep.by_node["Firm"]["dv01"])
    assert rep.results["limits"][0].status is LimitStatus.GREEN
    assert "Risk report" in str(rep)


def test_risk_engine_without_history_and_config(setup):
    md, book, _, _ = setup
    rep = RiskEngine().run(book, md, measures=("PV", "VAR"))
    assert "pv.total" in rep.metrics and "var.1d" not in rep.metrics
    assert any("No history" in n for n in rep.notes)
    with pytest.raises(ValueError):
        RiskEngine().run(book, md, measures=("NOPE",))
    eng = RiskEngine.from_config(lookback=100)
    assert eng.confidence == 0.99 and eng.horizon_days == 10 and eng.lookback == 100


def test_wrong_way_risk(setup):
    md, book, hist, _ = setup
    put = [book[2]]                                       # long SPX put: gains when credit deteriorates
    wwr = wrong_way_exposure(put, md, hist, "CR.ACME.5Y", shock_sigmas=3.0)
    assert wwr.conditional_exposure > wwr.base_exposure and wwr.ratio > 1.0
    assert str(next(iter(wwr.top_moves))) == "CR.ACME.5Y" or wwr.top_moves


def test_cli_demos(capsys):
    from qlrisk.demos import run_frtb_demo
    run_frtb_demo()
    assert "frtb_sa.total" in capsys.readouterr().out


def test_ccr_pipeline_credit_metrics():
    from qlrisk.engine import CCREngine
    with CCREngine() as e:
        m = e.calculate_ccr_metrics({"notional": 25e6, "mtm": 500_000, "counterparty_pd": 0.015,
                                     "counterparty_lgd": 0.5, "spread": 0.012})
        r = e.calculate_ccr_metrics({"notional": 25e6, "mtm": 500_000, "rating": "BBB", "recovery_rate": 0.4})
    assert m["el"] == pytest.approx(0.015 * 0.5 * 500_000)
    assert m["economic_capital"] > 0 and m["raroc"] > 0
    assert r["pd"] == pytest.approx(0.004) and r["lgd"] == pytest.approx(0.6)
    assert not [k for k in {**m, **r} if k.endswith("_error")]


def test_netting_set_exposure(setup):
    md, book, _, _ = setup
    d0 = md.valuation_date
    payer = P.InterestRateSwap("PAY", d0, d0, date(2031, 10, 9), 10e6, Currency.USD, "CP", fixed_rate=0.043, is_payer=True)
    recv = P.InterestRateSwap("REC", d0, d0, date(2031, 10, 9), 10e6, Currency.USD, "CP", fixed_rate=0.043, is_payer=False)
    rep = RiskEngine().run([payer, recv], md, measures=("EXPOSURE",))
    ns = rep.results["netting_sets"]["CP"]
    assert ns.mtm == pytest.approx(0.0, abs=1e-6) and ns.replacement_cost == pytest.approx(0.0, abs=1e-6)
    assert ns.addon == pytest.approx(0.0, abs=1e-6)                     # payer and receiver offset fully
    assert rep.metrics["exposure.saccr_ead_netted"] < rep.metrics["exposure.saccr_ead_trade_sum"]


def test_saccr_hedging_sets_and_margining(setup):
    from qlrisk.regulatory.saccr_netting import CSATerms, saccr_netting_sets
    md = setup[0]
    d0 = md.valuation_date
    pay = P.InterestRateSwap("P", d0, d0, date(2031, 10, 9), 10e6, Currency.USD, "CP", fixed_rate=0.043)
    short = P.InterestRateSwap("S", d0, d0, date(2027, 4, 9), 10e6, Currency.USD, "CP", fixed_rate=0.043, is_payer=False)
    res = saccr_netting_sets([pay, short], md)["CP"]
    d = {t.trade_id: t.signed_addon for t in res.trades}
    d1, d2 = d["S"], d["P"]                                     # buckets <1y and 1-5y
    assert res.addon_by_class["IR"] == pytest.approx((d1 ** 2 + d2 ** 2 + 1.4 * d1 * d2) ** 0.5)
    unmargined = saccr_netting_sets([pay], md)["CP"].ead
    margined = saccr_netting_sets([pay], md, csa={"CP": CSATerms(margined=True)})["CP"].ead
    assert margined < unmargined
    collateralised = saccr_netting_sets([pay], md, csa={"CP": CSATerms(collateral=1e9)})["CP"]
    assert collateralised.replacement_cost == 0.0 and collateralised.multiplier < 1.0


def test_xva_calculators_via_factory():
    from qlrisk.calculator import CalculatorType
    from qlrisk.calculator.factory import get_calculator_factory
    f = get_calculator_factory()
    grid, ee = [0.5, 1.0, 2.0, 3.0], [1e6, 1.2e6, 1.1e6, 0.8e6]
    curve = {1.0: 0.04, 5.0: 0.045}
    dva = f.create(CalculatorType.DVA, "d", {}).calculate({"exposure_profile": [-x for x in ee], "time_grid": grid,
                                                           "own_pd_curve": {1.0: 0.01, 5.0: 0.05}, "discount_curve": curve}).value
    assert dva.dva > 0
    fva = lambda s: f.create(CalculatorType.FVA, "f", {}).calculate({"exposure_profile": ee, "time_grid": grid,
                                                                     "funding_spread": s, "discount_curve": curve}).value
    assert abs(fva(0.02).__dict__[next(iter(fva(0.02).__dict__))]) > abs(fva(0.01).__dict__[next(iter(fva(0.01).__dict__))])
    for ct, data in [(CalculatorType.KVA, {"ead_profile": ee, "time_grid": grid, "counterparty_pd": 0.01,
                                            "counterparty_lgd": 0.6, "discount_curve": curve}),
                     (CalculatorType.MVA, {"initial_margin_profile": ee, "time_grid": grid, "funding_spread": 0.01,
                                            "discount_curve": curve})]:
        res = f.create(ct, ct.value, {}).calculate(data).value
        assert next(iter(res.__dict__.values())) != 0
