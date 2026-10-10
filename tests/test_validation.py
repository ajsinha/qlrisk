"""Tests for backtesting, P&L explain / PLA, stress library, reverse stress and liquidity VaR."""

from datetime import date

import numpy as np
import pytest

import qlrisk.products.python as P
from qlrisk.backtesting import (
    backtest_es, backtest_var, basel_multiplier, christoffersen_independence, kupiec_pof, traffic_light,
)
from qlrisk.calculator.python.liquidity_var import liquidity_adjusted_var, liquidity_cost
from qlrisk.data import MarketHistoryGenerator, create_sample_market_data
from qlrisk.engine import MarketRiskEngine
from qlrisk.pnl import explain_pnl, pla_test
from qlrisk.products.base import Currency
from qlrisk.riskfactors import ShockType, apply_shocks
from qlrisk.scenarios import STRESS_LIBRARY, historical_stress_scenarios, reverse_stress_test, stress_shocks

from conftest import VALUATION_DATE


def test_traffic_light_and_multiplier_match_basel():
    assert [traffic_light(k) for k in (0, 4, 5, 9, 10)] == ["green", "green", "yellow", "yellow", "red"]
    assert [basel_multiplier(k) for k in (4, 5, 7, 9, 12)] == [3.0, 3.4, 3.65, 3.85, 4.0]


def test_kupiec_and_christoffersen():
    assert kupiec_pof(2, 250, 0.99)[1] > 0.5 and kupiec_pof(10, 250, 0.99)[1] < 0.001
    clustered = [False] * 240 + [True] * 5 + [False] * 5
    spread = [i % 50 == 0 for i in range(250)]
    assert christoffersen_independence(clustered)[1] < 0.01 < christoffersen_independence(spread)[1]


def test_correct_model_passes_and_bad_model_fails():
    x = np.random.default_rng(0).standard_normal(1000)
    good = backtest_var(x, np.full(1000, 2.326), 0.99)
    bad = backtest_var(x, np.full(1000, 1.0), 0.99)
    assert good.passes() and good.zone == "green"
    assert not bad.passes() and bad.zone == "red"
    assert backtest_es(x, np.full(1000, 1.96), np.full(1000, 2.338), 0.975).zone == "green"
    assert backtest_es(x, np.full(1000, 1.0), np.full(1000, 1.2), 0.975).zone == "red"


def test_pla_zones():
    rng = np.random.default_rng(1)
    h = rng.standard_normal(250)
    assert pla_test(h, h + 0.05 * rng.standard_normal(250)).zone == "green"
    assert pla_test(h, rng.standard_normal(250)).zone == "red"


def test_liquidity_var():
    assert liquidity_cost({"A": 1e6, "B": -2e6}, {"A": 0.002, "B": 0.01}) == pytest.approx(1000 + 10000)
    assert liquidity_adjusted_var(100.0, {"A": 1000.0}, {"A": 0.02}, 4) == pytest.approx(210.0)


@pytest.fixture(scope="module")
def setup():
    md = create_sample_market_data(VALUATION_DATE)
    d0 = md.valuation_date
    book = [
        P.InterestRateSwap("IRS", d0, d0, date(2036, 10, 9), 25e6, Currency.USD, "CP", fixed_rate=0.043),
        P.CorporateBond("BOND", d0, d0, date(2031, 10, 9), 10e6, Currency.USD, "ACME", coupon=0.05, issuer="ACME"),
        P.EquityOption("EQO", d0, d0, date(2027, 4, 9), 5e6, Currency.USD, "CP", ticker="SPX", strike=5000.0,
                       is_call=False),
    ]
    hist = MarketHistoryGenerator(seed=7).generate(md, num_days=600, stress_start=200, stress_days=50)
    return md, book, hist


def test_explain_pnl_small_unexplained(setup):
    md, book, _ = setup
    moved = apply_shocks(md, {"EQ.SPX": -0.02, "IR.FWD.SOFR.10Y": 0.0005, "CR.ACME.5Y": 0.0003})
    moved.valuation_date = md.valuation_date
    ex = explain_pnl(book, md, moved, reporting_currency="USD")
    tot = ex.total()
    assert abs(tot["actual"]) > 1000
    assert abs(tot["unexplained"]) < 0.02 * abs(tot["actual"])
    assert set(ex.trades["EQO"].by_risk_class) >= {"EQ"}


def test_stress_library(setup):
    md, book, _ = setup
    assert len(STRESS_LIBRARY) == 9
    shocks = {str(s.factor): s for s in stress_shocks(md, STRESS_LIBRARY["2016_brexit"])}
    assert shocks["FX.GBPUSD"].size == pytest.approx(-0.11) and shocks["EQ.SPX"].shock_type is ShockType.RELATIVE
    usdjpy = stress_shocks(md, STRESS_LIBRARY["1998_ltcm_russia"])
    assert next(s for s in usdjpy if str(s.factor) == "FX.USDJPY").size == pytest.approx(1 / 1.12 - 1)
    scen = historical_stress_scenarios(md)
    assert len(scen) == 9
    results = MarketRiskEngine(reporting_currency="USD").stress_test(book, md, scen)
    assert results["2022_rates_shock"] > 0 > results["2008_gfc_lehman"]          # payer swap gains when rates rise


def test_reverse_stress_hits_target(setup):
    md, book, hist = setup
    res = reverse_stress_test(book, md, hist, loss=1_000_000)
    assert res.achieved_loss == pytest.approx(1_000_000, rel=1e-3)
    assert res.sigma_distance > 0 and res.top_moves
    pnl = MarketRiskEngine().scenario_pnl(book, md, res.scenario()).portfolio[0]
    assert pnl == pytest.approx(-1_000_000, rel=1e-3)


def test_engine_backtest(setup):
    md, book, hist = setup
    out = MarketRiskEngine(reporting_currency="USD").backtest(book, md, hist, test_days=200, lookback=250)
    assert out["var"].n == 200 and len(out["series"]["hpl"]) == 200
    assert out["pla"].spearman > 0.9
    assert out["var"].zone in ("green", "yellow")
