"""Tests for qlrisk.sensitivities: engine accuracy vs closed form, results, ladders."""

from datetime import date

import numpy as np
import pytest

from qlrisk.products.base import Currency, curve_value
from qlrisk.products.python import FXForward, InterestRateSwap
from qlrisk.riskfactors import RiskClass
from qlrisk.sensitivities import (
    FORWARD, FRTB_GIRR_VERTICES, SensitivityEngine, SensitivityMeasure, compute_sensitivities,
    fx_convert, rebucket,
)

from conftest import VALUATION_DATE, AnalyticEquityCall, AnalyticZeroCouponBond


# ------------------------------------------------------------ closed form

def test_zero_coupon_dv01_matches_closed_form(simple_md):
    # 5y ZCB sits exactly on the 5Y pillar: dPV/dr = -T * PV, so DV01 = -T * PV * 1bp
    zcb = AnalyticZeroCouponBond("ZCB", 5.0)
    t = zcb.time_to_maturity(simple_md)
    pv = zcb.price(simple_md).npv
    result = SensitivityEngine().compute(zcb, simple_md)
    total_dv01 = result.total(SensitivityMeasure.DV01)
    assert total_dv01 == pytest.approx(-t * pv * 1e-4, rel=1e-4)
    gamma = sum(r.gamma for r in result.filter(measure=SensitivityMeasure.DV01))
    assert gamma == pytest.approx(t * t * pv * 1e-8, rel=1e-2)


def test_key_rate_split_between_pillars(simple_md):
    # A 3y ZCB interpolates between 1Y and 5Y with weights 1/2, 1/2 (by time, approximately)
    zcb = AnalyticZeroCouponBond("ZCB3", 3.0)
    result = SensitivityEngine().compute(zcb, simple_md)
    by_factor = {str(k): v for k, v in result.by_factor().items()}
    assert set(by_factor) == {"IR.DISCOUNT.1Y", "IR.DISCOUNT.5Y", "IR.DISCOUNT.10Y"}
    assert by_factor["IR.DISCOUNT.10Y"] == pytest.approx(0.0, abs=1e-6)
    assert by_factor["IR.DISCOUNT.1Y"] == pytest.approx(by_factor["IR.DISCOUNT.5Y"], rel=0.01)


def test_equity_call_delta_gamma_vega_match_black_scholes(md):
    call = AnalyticEquityCall("C1", "AAPL", strike=200.0, expiry_years=1.0)
    exact = call.analytic_greeks(md)
    result = SensitivityEngine().compute(call, md)
    
    delta = result.get("C1", "EQ.AAPL")
    assert delta.measure is SensitivityMeasure.DELTA
    assert delta.derivative == pytest.approx(exact["delta"], rel=1e-3)
    spot = md.equity_prices["AAPL"]
    assert delta.value == pytest.approx(exact["delta"] * spot * 0.01, rel=1e-3)   # PV change per +1%
    assert delta.gamma / (0.01 * spot) ** 2 == pytest.approx(exact["gamma"], rel=1e-3)
    
    vega = result.get("C1", "VOL.eq_flat_vol")
    assert vega.measure is SensitivityMeasure.VEGA
    assert vega.value == pytest.approx(exact["vega"] * 0.01, rel=1e-3)


def test_forward_method_has_no_gamma(simple_md):
    result = SensitivityEngine(method=FORWARD).compute(AnalyticZeroCouponBond("Z", 5.0), simple_md)
    assert all(r.gamma is None for r in result)


# ----------------------------------------------------------- real products

def _swap(rate=0.044):
    return InterestRateSwap("IRS", VALUATION_DATE, VALUATION_DATE, date(2031, 10, 9), 10_000_000,
                            Currency.USD, "CP", fixed_rate=rate)


def test_payer_swap_dv01_magnitude(md):
    result = SensitivityEngine().compute(_swap(), md)
    dv01 = result.total(SensitivityMeasure.DV01)
    # 10mm 5y payer: DV01 ~ +notional * annuity(~4.5) * 1bp
    assert 3_500 < dv01 < 5_500
    assert result.errors == []


def test_parallel_dv01_matches_full_parallel_bump(md):
    from qlrisk.riskfactors import apply_shocks, curve_shocks, parallel
    swap = _swap()
    result = SensitivityEngine().compute(swap, md)
    up = apply_shocks(md, curve_shocks(md, shape=parallel(1e-4), risk_classes=[RiskClass.INTEREST_RATE],
                                       field=None))
    down = apply_shocks(md, curve_shocks(md, shape=parallel(-1e-4), risk_classes=[RiskClass.INTEREST_RATE],
                                         field=None))
    full = (swap.price(up).npv - swap.price(down).npv) / 2
    assert result.total(SensitivityMeasure.DV01) == pytest.approx(full, rel=1e-3)


def test_fx_forward_delta_and_reporting_currency(md):
    fxf = FXForward("FXF", VALUATION_DATE, date(2027, 10, 9), Currency.EUR, Currency.USD, 1_000_000, 1.10, "CP")
    usd = SensitivityEngine().compute(fxf, md, reporting_currency="USD")
    spot = md.fx_spots["EURUSD"]
    delta = usd.get("FXF", "FX.EURUSD")
    t = fxf.get_remaining_maturity(VALUATION_DATE)
    df = np.exp(-curve_value(md.discount_curve, t) * t)
    assert delta.value == pytest.approx(1_000_000 * spot * 0.01 * df, rel=1e-6)
    
    eur = SensitivityEngine().compute(fxf, md, reporting_currency="EUR")
    assert eur.base_pv["FXF"] == pytest.approx(usd.base_pv["FXF"] / spot)
    assert eur.get("FXF", "FX.EURUSD").value != pytest.approx(delta.value / spot)   # includes translation


def test_fx_convert_triangulates(md):
    assert fx_convert(md, 100.0, "EUR", "USD") == pytest.approx(108.5)
    assert fx_convert(md, 108.5, "USD", "EUR") == pytest.approx(100.0)
    assert fx_convert(md, 100.0, "EUR", "JPY") == pytest.approx(100.0 * 1.085 * 149.5)
    with pytest.raises(KeyError):
        fx_convert(md, 1.0, "USD", "CHF")


def test_dependency_detection_does_not_change_results(md):
    trades = [_swap(), AnalyticEquityCall("C1", "AAPL", 200.0, 1.0)]
    fast = SensitivityEngine().compute(trades, md)
    slow = SensitivityEngine(detect_dependencies=False).compute(trades, md)
    fast_map = {(r.trade_id, r.factor): r.value for r in fast}
    slow_map = {(r.trade_id, r.factor): r.value for r in slow if abs(r.value) > 1e-9}
    assert set(slow_map) <= set(fast_map)
    for k, v in slow_map.items():
        assert fast_map[k] == pytest.approx(v)


def test_threads_give_same_answer(md):
    trades = [_swap(), AnalyticEquityCall("C1", "AAPL", 200.0, 1.0)]
    a = SensitivityEngine().compute(trades, md).by_factor()
    b = SensitivityEngine(max_workers=4).compute(trades, md).by_factor()
    assert a.keys() == b.keys()
    assert all(a[k] == pytest.approx(b[k]) for k in a)


def test_errors_are_collected_not_raised(md):
    class Broken(AnalyticZeroCouponBond):
        def price(self, market_data):
            raise RuntimeError("boom")
    result = SensitivityEngine().compute([Broken("BAD", 2.0), AnalyticZeroCouponBond("OK", 2.0)], md)
    assert "OK" in result.base_pv and "BAD" not in result.base_pv
    assert result.errors and result.errors[0].trade_id == "BAD"


def test_duplicate_trade_ids_rejected(md):
    with pytest.raises(ValueError):
        SensitivityEngine().compute([AnalyticZeroCouponBond("X", 1.0), AnalyticZeroCouponBond("X", 2.0)], md)


# -------------------------------------------------------- theta, cross gamma

def test_theta_of_zero_coupon_bond(simple_md):
    zcb = AnalyticZeroCouponBond("ZCB", 5.0)
    result = SensitivityEngine().compute(zcb, simple_md, include_theta=True)
    pv = zcb.price(simple_md).npv
    # Rolling one day shortens T and rolls down the 1Y-5Y segment (slope 0.25%/yr), so the bond
    # accretes at the instantaneous forward r + T * r'(T) = 5% + 5 * 0.25% = 6.25% per year.
    assert result.theta()["ZCB"] == pytest.approx(pv * 0.0625 / 365.25, rel=0.01)


def test_cross_gamma_of_independent_factors_is_zero(md):
    call = AnalyticEquityCall("C1", "AAPL", 200.0, 1.0)
    result = SensitivityEngine().cross_gamma(call, md, ["EQ.AAPL", "VOL.eq_flat_vol", "FX.EURUSD"])
    by_pair = {(str(r.factor), str(r.factor2)): r.value for r in result}
    assert by_pair[("EQ.AAPL", "FX.EURUSD")] == pytest.approx(0.0, abs=1e-9)
    assert by_pair[("EQ.AAPL", "VOL.eq_flat_vol")] != pytest.approx(0.0, abs=1e-6)   # vanna


# ------------------------------------------------------------ aggregation

def test_aggregation_and_ladders(md):
    trades = [_swap(), AnalyticZeroCouponBond("Z7", 7.0), AnalyticEquityCall("C1", "AAPL", 200.0, 1.0)]
    result = compute_sensitivities(trades, md, include_theta=True)
    agg = result.aggregate(("risk_class", "measure"))
    assert (RiskClass.EQUITY, SensitivityMeasure.VEGA) in agg
    assert sum(agg.values()) == pytest.approx(result.total())
    
    ladder = result.ladder("discount_curve")
    assert ladder.total == pytest.approx(sum(r.value for r in result.filter(measure=SensitivityMeasure.DV01)
                                             if r.factor.field == "discount_curve"))
    frtb = result.ladder("discount_curve", vertices=FRTB_GIRR_VERTICES)
    assert frtb.total == pytest.approx(ladder.total)
    assert set(frtb.values) == set(FRTB_GIRR_VERTICES)
    rows = result.to_rows()
    assert rows and {"trade_id", "factor", "measure", "value"} <= set(rows[0])


def test_rebucket_preserves_total_and_splits_linearly():
    out = rebucket({4.0: 100.0, 0.1: 10.0, 40.0: 5.0}, [1.0, 3.0, 5.0, 10.0])
    assert out[3.0] == pytest.approx(50.0) and out[5.0] == pytest.approx(50.0)
    assert out[1.0] == pytest.approx(10.0) and out[10.0] == pytest.approx(5.0)
    assert sum(out.values()) == pytest.approx(115.0)


def test_merge(md):
    a = SensitivityEngine().compute(AnalyticZeroCouponBond("A", 2.0), md)
    b = SensitivityEngine().compute(AnalyticZeroCouponBond("B", 3.0), md)
    merged = a.merge(b)
    assert set(merged.base_pv) == {"A", "B"}
    with pytest.raises(ValueError):
        a.merge(a)
