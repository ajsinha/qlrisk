"""Tests for FRTB SA / IMA, Basel 2.5 and BA-CVA against hand calculations."""

import math
from datetime import date, timedelta

import numpy as np
import pytest

import qlrisk.products.python as P
from qlrisk.data import MarketHistoryGenerator, create_sample_market_data
from qlrisk.engine import MarketRiskEngine
from qlrisk.products.base import Currency
from qlrisk.regulatory import (
    CVACounterparty, CVAHedge, ba_cva, basel25_capital, frtb_sa_capital, ima_capital, ima_drc, imcc,
    liquidity_adjusted_es, rfet,
)
from qlrisk.regulatory.frtb_sa import DRCPosition, drc_charge, rrao_charge, sbm_capital
from qlrisk.regulatory.frtb_sa.parameters import scenario_rho
from qlrisk.regulatory.frtb_sa.sbm import FRTBSensitivity
from qlrisk.scenarios import historical_scenarios

from conftest import VALUATION_DATE


def S(rc, bucket, name, tenor, s, rw, rt="delta"):
    return FRTBSensitivity(rc, rt, bucket, name, tenor, s, rw)


def test_correlation_scenarios():
    assert scenario_rho(0.5, "high") == pytest.approx(0.625)
    assert scenario_rho(0.5, "low") == pytest.approx(0.375)       # max(2*0.5-1, 0.75*0.5)
    assert scenario_rho(0.9, "high") == 1.0


def test_girr_within_bucket():
    fs = [S("GIRR", "USD", "SOFR", 1.0, 1e6, 0.01), S("GIRR", "USD", "SOFR", 5.0, 1e6, 0.01)]
    rho = max(math.exp(-0.03 * 4 / 1), 0.4)
    expected = {s: math.sqrt(2e8 + 2 * scenario_rho(rho, s) * 1e8) for s in ("low", "medium", "high")}
    res = sbm_capital(fs)
    assert res.total == pytest.approx(max(expected.values())) and res.scenario == "high"


def test_offsetting_buckets_and_no_diversification_bucket():
    fx = [S("FX", "EUR", "EUR", None, 1e6, 0.15), S("FX", "JPY", "JPY", None, -1e6, 0.15)]
    ws = 0.15e6
    med = math.sqrt(2 * ws * ws - 2 * 0.6 * ws * ws)
    assert sbm_capital(fx).by_scenario["medium"] == pytest.approx(med)
    eq_other = [S("EQ", 11, "A", None, 1e6, 0.70), S("EQ", 11, "B", None, -1e6, 0.70)]
    assert sbm_capital(eq_other).total == pytest.approx(1.4e6)                   # sum of |WS|


def test_curvature_long_option_is_zero_short_option_positive():
    md = create_sample_market_data(VALUATION_DATE)
    d0 = md.valuation_date
    long_put = P.EquityOption("L", d0, d0, date(2027, 4, 9), 5e6, Currency.USD, "CP", ticker="SPX", strike=5000.0,
                              is_call=False)
    short_put = P.EquityOption("S", d0, d0, date(2027, 4, 9), 5e6, Currency.USD, "CP", ticker="SPX", strike=5000.0,
                               is_call=False, is_long=False)
    kw = dict(equity_buckets={"SPX": 12}, vol_underlyings={"eq_vol": "SPX"})
    assert frtb_sa_capital([long_put], md, **kw).sbm.by_component[("EQ", "curvature")] == 0.0
    assert frtb_sa_capital([short_put], md, **kw).sbm.by_component[("EQ", "curvature")] > 0.0


def test_drc_jtd_netting_and_hbr():
    bond = DRCPosition("ACME", "BBB", 10e6, 9.8e6, 5.0)
    assert bond.jtd == pytest.approx(0.75 * 10e6 - 0.2e6)
    hedge = DRCPosition("ACME", "BBB", -10e6, -10e6, 5.0)
    assert drc_charge([bond, hedge]).total == 0.0          # net short obligor, no longs to offset: floored at 0
    other_short = DRCPosition("GLOBEX", "BB", -4e6, -4e6, 0.5)
    res = drc_charge([bond, other_short])
    hbr = bond.jtd / (bond.jtd + abs(other_short.jtd))
    assert other_short.jtd == pytest.approx(-0.75 * 4e6 * 0.5)
    assert res.total == pytest.approx(0.06 * bond.jtd - hbr * 0.15 * abs(other_short.jtd))


def test_rrao():
    md = create_sample_market_data(VALUATION_DATE)
    d0 = md.valuation_date
    bar = P.FXBarrierOption("BAR", d0, d0, date(2027, 4, 9), 5e6, Currency.EUR, "CP", pair="EURUSD")
    fwd = P.EquityForward("F", d0, d0, date(2027, 4, 9), 5e6, Currency.USD, "CP", ticker="SPX")
    assert rrao_charge([bar, fwd])["total"] == pytest.approx(5000.0)
    assert rrao_charge([fwd], exotic=["F"])["total"] == pytest.approx(50000.0)


def test_frtb_sa_end_to_end():
    md = create_sample_market_data(VALUATION_DATE)
    d0 = md.valuation_date
    book = [P.InterestRateSwap("IRS", d0, d0, date(2036, 10, 9), 25e6, Currency.USD, "CP", fixed_rate=0.043),
            P.CorporateBond("B", d0, d0, date(2031, 10, 9), 10e6, Currency.USD, "ACME", coupon=0.05, issuer="ACME"),
            P.CommodityForward("C", d0, d0, date(2027, 10, 9), 5e6, Currency.USD, "CP", commodity="WTI", strike=70.0)]
    res = frtb_sa_capital(book, md, credit_buckets={"ACME": 4}, ratings={"ACME": "BBB"})
    s = res.summary()
    assert s["TOTAL"] == pytest.approx(s["SBM"] + s["DRC"] + s["RRAO"])
    assert s["CM_delta"] == pytest.approx(0.35 * book[2].price(md).npv / 0.01 * 0.01 + 0.35 * 5e6, rel=0.2)
    assert {"GIRR_delta", "CSR_delta", "CM_delta"} <= set(s)


def test_ima_pieces():
    md = create_sample_market_data(VALUATION_DATE)
    hist = MarketHistoryGenerator(seed=7).generate(md, num_days=600, stress_start=200, stress_days=50)
    d0 = md.valuation_date
    book = [P.InterestRateSwap("IRS", d0, d0, date(2036, 10, 9), 25e6, Currency.USD, "CP", fixed_rate=0.043)]
    eng = MarketRiskEngine(reporting_currency="USD")
    sens = eng.sensitivities(book, md)
    ten = historical_scenarios(hist, horizon=10).restrict_to(md)
    pnl_fn = lambda s: eng.scenario_pnl(book, md, s, "taylor", sensitivities=sens).portfolio
    all10 = liquidity_adjusted_es(pnl_fn, ten, {k: 10 for k in ten.factors})
    from qlrisk.calculator.python.var_calculators import expected_shortfall
    assert all10["es"] == pytest.approx(expected_shortfall(pnl_fn(ten), 0.975))
    longer = liquidity_adjusted_es(pnl_fn, ten, {k: 60 for k in ten.factors})
    assert longer["es"] == pytest.approx(all10["es"] * math.sqrt(6))           # sqrt(1 + 1 + 2 + 2) cascade
    r = imcc(eng, book, md, hist)
    assert r.imcc > 0 and r.ratio >= 1.0 and r.stress_window[0] < r.stress_window[1]


def test_rfet_ima_capital_and_drc():
    d0 = VALUATION_DATE
    assert rfet([d0 - timedelta(days=i) for i in range(0, 360, 3)], d0)                 # 120 obs
    assert not rfet([d0 - timedelta(days=i) for i in range(0, 360, 20)], d0)             # 18 obs
    gappy = [d0 - timedelta(days=i) for i in range(0, 100, 3)]                           # 34 obs, all recent
    assert not rfet(gappy, d0)
    assert ima_capital(10.0, 2.0, 1.0, multiplier=1.5) == pytest.approx(18.0)   # max(12, 1.5*10+2) + DRC 1
    assert ima_capital(10.0, 2.0, imcc_avg60=5.0, ses_avg60=1.0) == pytest.approx(12.0)
    single = [DRCPosition("ACME", "BBB", 10e6, 10e6, 5.0)]
    assert ima_drc(single, n_sims=50_000)["drc"] == pytest.approx(7.5e6)


def test_basel25_and_ba_cva():
    out = basel25_capital([1e6] * 60, [2e6] * 60, exceptions=0)
    assert out["capital"] == pytest.approx(9e6)
    cp = CVACounterparty("BANK", "financial", True, [(10e6, 5.0)])
    df = (1 - math.exp(-0.25)) / 0.25
    scva = 0.05 / 1.4 * 5.0 * 10e6 * df
    reduced = ba_cva([cp])
    assert reduced["scva"]["BANK"] == pytest.approx(scva)
    assert reduced["capital"] == pytest.approx(0.65 * scva)               # single counterparty: K = SCVA
    hedged = ba_cva([CVACounterparty("BANK", "financial", True, [(10e6, 5.0)], [CVAHedge(5e6, 5.0)])])
    assert hedged["capital"] < reduced["capital"]
