"""Tests for qlrisk.riskfactors: taxonomy, mapping, shocks and dependency detection."""

from datetime import date

import pytest

from qlrisk.products.base import Currency, MarketData, curve_value
from qlrisk.products.python import FXForward, InterestRateSwap, Swaption
from qlrisk.riskfactors import (
    FactorKind, RiskClass, RiskFactorKey, Shock, ShockType, apply_shocks, butterfly, clone_market_data,
    curve_shocks, enumerate_risk_factors, format_tenor, get_factor_value, parallel, parse_tenor,
    set_factor_value, set_factors, twist,
)

from conftest import VALUATION_DATE


# ----------------------------------------------------------------- curve_value

class TestCurveValue:
    curve = {1.0: 0.04, 5.0: 0.05, 10.0: 0.06}

    def test_exact_pillar(self):
        assert curve_value(self.curve, 5.0) == 0.05

    def test_linear_interpolation(self):
        assert curve_value(self.curve, 3.0) == pytest.approx(0.045)

    def test_flat_extrapolation(self):
        assert curve_value(self.curve, 0.1) == 0.04
        assert curve_value(self.curve, 30.0) == 0.06

    def test_empty_curve_uses_default(self):
        assert curve_value({}, 3.0, 0.07) == 0.07


# -------------------------------------------------------------------- taxonomy

class TestTaxonomy:
    @pytest.mark.parametrize("tenor,label", [(0.25, "3M"), (0.5, "6M"), (1.0, "1Y"), (30.0, "30Y"),
                                             (1 / 12, "1M"), (0.1, "0.1Y"), (2.5, "2.5Y")])
    def test_tenor_round_trip(self, tenor, label):
        assert format_tenor(tenor) == label
        assert parse_tenor(label) == pytest.approx(tenor)

    @pytest.mark.parametrize("text", ["IR.DISCOUNT.5Y", "IR.FWD.SOFR.3M", "IR.REF.SOFR", "FX.EURUSD",
                                      "CR.ACME.5Y", "EQ.AAPL", "DIV.AAPL.1Y", "BOND.UST10Y",
                                      "VOL.swaption_vol", "VOL.cap_vol.2Y", "VOL.eq_vol.1Y.100", "MISC.sofr_rate"])
    def test_key_string_round_trip(self, text):
        assert str(RiskFactorKey.parse(text)) == text

    def test_classification(self):
        assert RiskFactorKey.parse("IR.FWD.SOFR.5Y").risk_class is RiskClass.INTEREST_RATE
        assert RiskFactorKey.parse("FX.EURUSD").kind is FactorKind.SPOT
        assert RiskFactorKey.parse("CR.ACME.5Y").kind is FactorKind.SPREAD
        assert RiskFactorKey.parse("VOL.swaption_vol").risk_class is RiskClass.INTEREST_RATE
        assert RiskFactorKey.parse("VOL.fx_vol").risk_class is RiskClass.FX
        assert RiskFactorKey.parse("VOL.eq_vol.1Y").risk_class is RiskClass.EQUITY
        assert RiskFactorKey.parse("MISC.sofr_rate").risk_class is RiskClass.OTHER

    def test_invalid_keys(self):
        with pytest.raises(ValueError):
            RiskFactorKey.parse("NOPE.X")
        with pytest.raises(ValueError):
            RiskFactorKey.parse("FX")


# --------------------------------------------------------------------- mapping

class TestMapping:
    def test_enumerate_covers_every_field(self, simple_md):
        simple_md.sofr_rate = 0.043
        keys = {str(k) for k in enumerate_risk_factors(simple_md)}
        assert {"IR.DISCOUNT.1Y", "IR.DISCOUNT.10Y", "IR.FWD.SOFR.5Y", "FX.EURUSD", "CR.ACME.5Y",
                "EQ.AAPL", "VOL.swaption_vol", "VOL.cap_vol.2Y", "VOL.eq_vol.1Y.90", "MISC.sofr_rate"} <= keys
        assert len(keys) == 15   # 3 discount + 2 SOFR + 2 FX + 5 vol + 1 credit + 1 equity + 1 misc

    def test_enumerate_filters(self, simple_md):
        fx = enumerate_risk_factors(simple_md, risk_classes=[RiskClass.FX])
        assert [str(k) for k in fx] == ["FX.EURUSD", "FX.USDJPY"]
        disc = enumerate_risk_factors(simple_md, fields=["discount_curve"])
        assert len(disc) == 3

    def test_get_and_set(self, simple_md):
        clone = clone_market_data(simple_md)
        set_factor_value(clone, "VOL.eq_vol.1Y.100", 0.3)
        set_factor_value(clone, "IR.FWD.SOFR.5Y", 0.06)
        assert get_factor_value(clone, "VOL.eq_vol.1Y.100") == 0.3
        assert get_factor_value(clone, "IR.FWD.SOFR.5Y") == 0.06
        assert simple_md.volatility_surfaces["eq_vol"][1.0][100.0] == 0.20
        assert simple_md.forward_curves["SOFR"][5.0] == 0.051

    def test_tenor_lookup_tolerates_rounding(self):
        md = MarketData(valuation_date=VALUATION_DATE, discount_curve={1 / 12: 0.04})
        assert get_factor_value(md, RiskFactorKey("discount_curve", tenor=0.0833333333333)) == 0.04

    def test_missing_factor_raises(self, simple_md):
        with pytest.raises(KeyError):
            get_factor_value(simple_md, "FX.GBPUSD")


# ---------------------------------------------------------------------- shocks

class TestShocks:
    def test_shock_types(self, simple_md):
        out = apply_shocks(simple_md, [
            Shock(RiskFactorKey.parse("IR.DISCOUNT.5Y"), 0.0001, ShockType.ABSOLUTE),
            Shock(RiskFactorKey.parse("FX.EURUSD"), 0.10, ShockType.RELATIVE),
            Shock(RiskFactorKey.parse("EQ.AAPL"), 0.0, ShockType.LOG),
        ])
        assert out.discount_curve[5.0] == pytest.approx(0.0501)
        assert out.fx_spots["EURUSD"] == pytest.approx(1.21)
        assert out.equity_prices["AAPL"] == pytest.approx(190.0)

    def test_copy_on_write(self, simple_md):
        out = apply_shocks(simple_md, {"IR.DISCOUNT.5Y": 0.01})
        assert simple_md.discount_curve[5.0] == 0.05
        assert out.fx_spots is simple_md.fx_spots            # untouched field is shared
        assert out.discount_curve is not simple_md.discount_curve

    def test_nested_copy_is_deep(self, simple_md):
        out = apply_shocks(simple_md, {"VOL.eq_vol.1Y.100": 0.05})
        assert out.volatility_surfaces["eq_vol"][1.0][100.0] == pytest.approx(0.25)
        assert simple_md.volatility_surfaces["eq_vol"][1.0][100.0] == 0.20

    def test_curve_shapes(self):
        assert parallel(0.01)(7.0) == 0.01
        tw = twist(-0.01, 0.01, 2.0, 10.0)
        assert tw(1.0) == -0.01 and tw(6.0) == pytest.approx(0.0) and tw(20.0) == 0.01
        bf = butterfly(0.0, 0.01, 2.0, 5.0, 10.0)
        assert bf(5.0) == 0.01 and bf(1.0) == 0.0 and bf(30.0) == 0.0

    def test_curve_shocks(self, simple_md):
        shocks = curve_shocks(simple_md, "discount_curve", shape=parallel(0.0010))
        assert len(shocks) == 3
        out = apply_shocks(simple_md, shocks)
        assert all(out.discount_curve[t] == pytest.approx(simple_md.discount_curve[t] + 0.001) for t in out.discount_curve)
        sofr_only = curve_shocks(simple_md, "forward_curves", "SOFR")
        assert {k.name for k in (s.factor for s in sofr_only)} == {"SOFR"}

    def test_set_factors(self, simple_md):
        out = set_factors(simple_md, {"FX.EURUSD": 1.2})
        assert out.fx_spots["EURUSD"] == 1.2 and simple_md.fx_spots["EURUSD"] == 1.10


# ------------------------------------------------------- dependency detection

class TestDependencies:
    def test_swap_depends_on_its_curves_only(self, md):
        irs = InterestRateSwap("IRS", VALUATION_DATE, VALUATION_DATE, date(2031, 10, 9), 1e7,
                               Currency.USD, "CP", fixed_rate=0.044)
        fields = {(k.field, k.name) for k in irs.risk_factors(md)}
        assert fields == {("discount_curve", None), ("forward_curves", "SOFR")}

    def test_fx_forward_depends_on_pair_and_discounting(self, md):
        fxf = FXForward("FXF", VALUATION_DATE, date(2027, 10, 9), Currency.EUR, Currency.USD, 1e6, 1.10, "CP")
        keys = fxf.risk_factors(md)
        assert RiskFactorKey("fx_spots", "EURUSD") in keys
        assert RiskFactorKey("fx_spots", "GBPUSD") not in keys
        assert any(k.field == "discount_curve" for k in keys)

    def test_swaption_depends_on_vol(self, md):
        sw = Swaption("SW", VALUATION_DATE, date(2027, 10, 9), date(2027, 10, 9), date(2032, 10, 9), 1e7,
                      Currency.USD, "CP", 0.045)
        assert RiskFactorKey("volatility_surfaces", "swaption_vol") in sw.risk_factors(md)
