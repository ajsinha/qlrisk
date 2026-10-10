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


# ------------------------------------------------------------------ SA-CVA (MAR50)

from qlrisk.regulatory.sa_cva import CVASensitivity, cva_from_profile, sa_cva_aggregate, sa_cva_capital


def test_sa_cva_ir_bucket_and_hedge_disallowance():
    s = [CVASensitivity("IR", "delta", "USD", 1.0, 1e6, 0.0, 0.0111), CVASensitivity("IR", "delta", "USD", 5.0, 1e6, 0.0, 0.0074)]
    w1, w5 = 0.0111e6, 0.0074e6
    assert sa_cva_aggregate(s).total == pytest.approx(math.sqrt(w1 ** 2 + w5 ** 2 + 2 * 0.72 * w1 * w5))
    hedged = [CVASensitivity("IR", "delta", "USD", 1.0, 1e6, -1e6, 0.0111)]
    assert sa_cva_aggregate(hedged).total == pytest.approx(math.sqrt(0.01) * 0.0111e6)     # only R x hedge^2 left


def test_sa_cva_correlations():
    a = CVASensitivity("CCS", "delta", "3", ("A", 5.0), 1e6, 0, 0.03, {"ig": True})
    b = CVASensitivity("CCS", "delta", "3", ("B", 1.0), 1e6, 0, 0.03, {"ig": False})
    rho = 0.9 * 0.5 * 0.8
    assert sa_cva_aggregate([a, b]).total == pytest.approx(math.sqrt(2 * 0.03e6 ** 2 * (1 + rho)))
    x = CVASensitivity("RCS", "delta", 1, None, 1e6, 0, 0.005)
    y = CVASensitivity("RCS", "delta", 9, None, 1e6, 0, 0.04)            # HY local government vs IG sovereign
    wx, wy = 0.005e6, 0.04e6
    assert sa_cva_aggregate([x, y]).total == pytest.approx(math.sqrt(wx ** 2 + wy ** 2 + 2 * (0.75 / 2) * wx * wy))


def test_sa_cva_end_to_end_hedge_reduces_capital():
    md = create_sample_market_data(VALUATION_DATE)
    d0 = md.valuation_date
    fn = cva_from_profile("ACME", [0.5, 1, 2, 3, 4, 5], [2e6, 3e6, 3.5e6, 3e6, 2e6, 1e6])
    bare = sa_cva_capital(fn, md, {"ACME": ("3", True)})
    hedge = P.CreditDefaultSwap("H", d0, d0, date(2031, 10, 9), 3e6, Currency.USD, "DEALER", reference="ACME")
    hedged = sa_cva_capital(fn, md, {"ACME": ("3", True)}, hedges=[hedge])
    assert bare.by_component[("CCS", "delta")] > 0 and bare.by_component[("IR", "delta")] > 0
    assert hedged.total < bare.total


def test_csr_sector_table_and_two_factor_drc():
    from qlrisk.regulatory.frtb_sa.sbm import _gamma
    assert _gamma("CSR", 1, 2, None) == 0.75 and _gamma("CSR", 3, 11, None) == 0.5        # same sector, IG vs HY
    assert _gamma("CSR", 1, 10, None) == pytest.approx(0.375) and _gamma("CSR", 17, 18, None) == 0.75
    assert _gamma("CSR", 4, 16, None) == 0.0 and _gamma("CSR", 4, 5, 0.2) == 0.2            # flat override
    names = [DRCPosition(f"N{i}", "B", 1e6, 1e6, 1.0) for i in range(30)]
    one_sector = ima_drc(names, n_sims=40_000, sectors={p.obligor: "S" for p in names})["drc"]
    spread = ima_drc(names, n_sims=40_000, sectors={p.obligor: f"S{i % 10}" for i, p in enumerate(names)})["drc"]
    assert one_sector > spread
