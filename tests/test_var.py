"""Tests for VaR / ES math, scenarios, P&L matrices and the MarketRiskEngine."""

from datetime import date

import numpy as np
import pytest

import qlrisk.products.python as P
from qlrisk.calculator import CalculatorType
from qlrisk.calculator.factory import get_calculator_factory
from qlrisk.calculator.python.var_calculators import (
    expected_shortfall, parametric_es, parametric_var, value_at_risk,
)
from qlrisk.data import MarketHistoryGenerator, create_sample_market_data
from qlrisk.engine import TAYLOR, MarketRiskEngine
from qlrisk.pnl import PnLMatrix
from qlrisk.products.base import Currency
from qlrisk.riskfactors import Shock, ShockType
from qlrisk.scenarios import (
    ScenarioSet, age_weights, filtered_historical_scenarios, find_stress_window, historical_scenarios,
    monte_carlo_scenarios,
)

from conftest import VALUATION_DATE

LOSSES = -np.arange(1, 251, dtype=float)      # P&L -1 ... -250


# ---------------------------------------------------------------- pure math

def test_historical_var_and_es_definitions():
    assert value_at_risk(LOSSES, 0.99) == 248.0                       # 3rd worst of 250
    assert expected_shortfall(LOSSES, 0.99) == pytest.approx((250 + 249 + 0.5 * 248) / 2.5)
    assert expected_shortfall(-np.arange(1, 101.0), 0.95) == pytest.approx(98.0)
    assert value_at_risk(LOSSES, 0.99, np.ones(250)) == value_at_risk(LOSSES, 0.99)


def test_weights_shift_the_tail():
    w = np.ones(250)
    w[LOSSES.argmin()] = 1000.0                                         # worst scenario dominates
    assert value_at_risk(LOSSES, 0.99, w) == 250.0
    with pytest.raises(ValueError):
        value_at_risk(LOSSES, 0.99, -np.ones(250))
    with pytest.raises(ValueError):
        value_at_risk(LOSSES, 1.5)


def test_parametric_formulas():
    assert parametric_var(0, 1, 0.99) == pytest.approx(2.3263, abs=1e-4)
    assert parametric_es(0, 1, 0.975) == pytest.approx(2.3378, abs=1e-4)
    assert parametric_var(0, 1, 0.99, skew=-0.5) > parametric_var(0, 1, 0.99)       # left skew fattens loss tail
    assert parametric_var(0, 1, 0.99, excess_kurtosis=3) > parametric_var(0, 1, 0.99)


def test_factory_calculators():
    f = get_calculator_factory()
    assert f.create(CalculatorType.VAR, "v", {}).calculate({"pnl": LOSSES, "confidence": 0.99}).value == 248.0
    es = f.create(CalculatorType.EXPECTED_SHORTFALL, "e", {"method": "parametric"})
    assert es.calculate({"mean": 0.0, "std": 1.0}).value == pytest.approx(2.3378, abs=1e-4)


# ---------------------------------------------------------------- P&L matrix

def test_component_contributions_sum_to_total():
    rng = np.random.default_rng(0)
    m = PnLMatrix(["A", "B", "C"], list(range(500)), rng.standard_normal((3, 500)) * [[1], [2], [3]])
    for res in (m.var(0.99), m.es(0.975)):
        assert sum(res.contributions.values()) == pytest.approx(res.value)
    assert set(m.incremental()) == {"A", "B", "C"}
    assert sum(m.standalone().values()) > m.var(0.99).value                            # diversification
    g = m.group({"A": "desk1", "B": "desk1", "C": "desk2"})
    assert g.trade_ids == ["desk1", "desk2"] and np.allclose(g.portfolio, m.portfolio)


# ---------------------------------------------------------------- scenarios

@pytest.fixture(scope="module")
def market():
    md = create_sample_market_data(VALUATION_DATE)
    hist = MarketHistoryGenerator(seed=7).generate(md, num_days=750, stress_start=300, stress_days=60)
    d0 = md.valuation_date
    linear = [
        P.InterestRateSwap("IRS", d0, d0, date(2036, 10, 9), 25e6, Currency.USD, "CP", fixed_rate=0.043),
        P.CorporateBond("BOND", d0, d0, date(2031, 10, 9), 10e6, Currency.USD, "ACME", coupon=0.05, issuer="ACME"),
        P.FXForward("FXF", d0, date(2027, 10, 9), Currency.EUR, Currency.USD, 10e6, 1.10, "CP"),
    ]
    option = P.EquityOption("EQO", d0, d0, date(2027, 4, 9), 5e6, Currency.USD, "CP", ticker="SPX",
                            strike=5000.0, is_call=False)
    return md, hist, linear, option


def test_scenario_generators(market):
    md, hist, _, _ = market
    h = historical_scenarios(hist, lookback=250)
    assert len(h) == 250 and h.labels[-1] == hist.dates[-1]
    assert len(historical_scenarios(hist, lookback=250, horizon=10)) == 241               # overlapping 10d
    w = historical_scenarios(hist, lookback=250, age_weighting=0.99).weights
    assert w.sum() == pytest.approx(1.0) and w[-1] > w[0]
    assert np.allclose(age_weights(3, 0.5), np.array([1, 2, 4]) / 7)
    f = filtered_historical_scenarios(hist, lookback=250)
    assert f.returns.shape == h.returns.shape and f.method == "filtered_historical"
    mc = monte_carlo_scenarios(hist, n=20000, lookback=250, seed=3)
    spx = h.factors.index(next(k for k in h.factors if str(k) == "EQ.SPX"))
    assert mc.returns[:, spx].std() == pytest.approx(np.nanstd(h.returns[:, spx]), rel=0.05)


def test_scenario_set_from_shocks(market):
    md, *_ = market
    s = ScenarioSet.from_shocks({"crash": [Shock("EQ.SPX", -0.3, ShockType.RELATIVE)],
                                 "rates": [Shock("IR.DISCOUNT.5Y", 0.01)]})
    assert len(s) == 2 and s.labels == ["crash", "rates"]
    assert s.market_data(0, md).equity_prices["SPX"] == pytest.approx(md.equity_prices["SPX"] * 0.7)
    assert s.market_data(0, md).discount_curve == md.discount_curve                        # NaN = no move


def test_stress_window_finds_injected_stress():
    rng = np.random.default_rng(1)
    pnl = rng.standard_normal(1000)
    pnl[600:700] *= 5
    w = find_stress_window(pnl, list(range(1000)), window=250)
    overlap = min(w.end_index, 700) - max(w.start_index, 600)
    assert overlap >= 80                          # the stressed window covers the injected stress


# ---------------------------------------------------------------- engine

def test_full_and_taylor_agree_for_linear_book(market):
    md, hist, linear, _ = market
    eng = MarketRiskEngine(reporting_currency="USD")
    scen = historical_scenarios(hist, lookback=250)
    full = eng.var(linear, md, scen)
    taylor = eng.var(linear, md, scen, method=TAYLOR)
    assert taylor.value == pytest.approx(full.value, rel=0.02)
    assert not eng.scenario_pnl(linear, md, scen).errors


def test_parametric_matches_monte_carlo_for_linear_book(market):
    md, hist, linear, _ = market
    eng = MarketRiskEngine(reporting_currency="USD")
    sens = eng.sensitivities(linear, md)
    pvar = eng.parametric_var(linear, md, hist, lookback=250, sensitivities=sens)
    mc = monte_carlo_scenarios(hist, n=40000, lookback=250, seed=11)
    mcvar = eng.scenario_pnl(linear, md, mc, TAYLOR, order=1, sensitivities=sens).var(0.99)
    assert pvar.value == pytest.approx(mcvar.value, rel=0.03)
    assert sum(pvar.contributions.values()) == pytest.approx(pvar.value)
    ten = eng.parametric_var(linear, md, hist, lookback=250, horizon_days=10, sensitivities=sens)
    assert ten.value == pytest.approx(pvar.value * np.sqrt(10))


def test_option_book_es_exceeds_var_and_stressed_var(market):
    md, hist, linear, option = market
    eng = MarketRiskEngine(reporting_currency="USD")
    book = linear + [option]
    scen = historical_scenarios(hist, lookback=250)
    assert eng.es(book, md, scen, 0.99).value >= eng.var(book, md, scen, 0.99).value
    svar = eng.stressed_var(book, md, hist, window=250, horizon_days=10)
    normal_10d = eng.var(book, md, historical_scenarios(hist, lookback=250, horizon=10, sqrt_scaling=True))
    assert svar.value > normal_10d.value
    start, end = hist.dates.index(svar.metadata["window_start"]), hist.dates.index(svar.metadata["window_end"])
    assert start <= 330 and end >= 330                                                    # overlaps the stress
    summary = eng.summary(book, md, hist)
    assert set(summary) == {"var_1d_99", "es_1d_975", "var_10d_99", "parametric_var_1d_99", "stressed_var_10d_99"}


def test_factory_cache_respects_config():
    from qlrisk.calculator import CalculatorFactory
    f = CalculatorFactory()
    a = f.get_pd_calculator(config={"model": "structural"})
    b = f.get_pd_calculator(config={"model": "transition_matrix"})
    assert a is not b and b.calculate({"credit_rating": "BBB"}).value == pytest.approx(0.004)
    assert f.get_pd_calculator(config={"model": "transition_matrix"}) is b
