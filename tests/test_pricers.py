"""Tests for the shared analytic pricers (products/python/_pricing.py)."""

from datetime import date

import numpy as np
import pytest

import qlrisk.products.python as P
from qlrisk.products.base import Currency, MarketData, curve_value
from qlrisk.riskfactors import RiskClass
from qlrisk.sensitivities import SensitivityEngine

from conftest import VALUATION_DATE

MAT = date(2031, 10, 9)          # 5y


def make(cls_name, maturity=MAT, notional=1_000_000, ccy=Currency.USD, **kw):
    cls = getattr(P, cls_name)
    return cls(f"T-{cls_name}", VALUATION_DATE, VALUATION_DATE, maturity, notional, ccy, "CP", **kw)


# product -> (kwargs, risk class its PV must respond to)
CASES = {
    "TreasuryBond": ({"coupon": 0.04}, RiskClass.INTEREST_RATE),
    "CorporateBond": ({"coupon": 0.05, "issuer": "ACME"}, RiskClass.CREDIT),
    "ZeroCouponBond": ({}, RiskClass.INTEREST_RATE),
    "TreasuryBill": ({}, RiskClass.INTEREST_RATE),
    "CertificateOfDeposit": ({"rate": 0.045}, RiskClass.INTEREST_RATE),
    "FloatingRateNote": ({"spread": 0.005, "issuer": "GLOBEX"}, RiskClass.CREDIT),
    "Repo": ({"rate": 0.043}, RiskClass.INTEREST_RATE),
    "CommonStock": ({"ticker": "AAPL"}, RiskClass.EQUITY),
    "ETF": ({"ticker": "SPX"}, RiskClass.EQUITY),
    "EquityOption": ({"ticker": "AAPL", "strike": 200.0}, RiskClass.EQUITY),
    "Warrant": ({"ticker": "MSFT"}, RiskClass.EQUITY),
    "EquityForward": ({"ticker": "SPX"}, RiskClass.EQUITY),
    "IndexFuture": ({"ticker": "SPX", "is_future": True}, RiskClass.EQUITY),
    "FXOption": ({"pair": "EURUSD"}, RiskClass.FX),
    "FXDigitalOption": ({"pair": "EURUSD"}, RiskClass.FX),
    "FXBarrierOption": ({"pair": "EURUSD", "strike": 1.10, "barrier": 1.60}, RiskClass.FX),
    "NonDeliverableForward": ({"pair": "USDJPY"}, RiskClass.FX),
    "CreditDefaultSwap": ({"reference": "ACME"}, RiskClass.CREDIT),
    "CDSIndex": ({"reference": "GLOBEX"}, RiskClass.CREDIT),
    "CommodityForward": ({"commodity": "WTI"}, RiskClass.COMMODITY),
    "CommoditySwap": ({"commodity": "BRENT"}, RiskClass.COMMODITY),
    "CommodityOption": ({"commodity": "GOLD"}, RiskClass.COMMODITY),
    "CrossCurrencySwap": ({"pair": "EURUSD", "foreign_curve": "ESTR"}, RiskClass.FX),
}


@pytest.mark.parametrize("name", sorted(CASES))
def test_product_prices_and_responds_to_its_market(name, md):
    kwargs, risk_class = CASES[name]
    trade = make(name, **kwargs)
    assert np.isfinite(trade.price(md).npv)
    result = SensitivityEngine().compute(trade, md)
    assert not result.errors
    assert abs(result.total(risk_class=risk_class)) > 1e-6, f"{name} has no {risk_class.value} sensitivity"


def test_par_bond_prices_at_par():
    md = MarketData(valuation_date=VALUATION_DATE, discount_curve={1.0: 0.05, 10.0: 0.05})
    r = 2 * (np.exp(0.05 / 2) - 1)                 # semi-annual coupon equivalent to 5% continuous
    bond = make("TreasuryBond", maturity=date(2031, 4, 9), coupon=r)   # 4.5y: whole semi-annual periods
    assert bond.price(md).npv == pytest.approx(1_000_000, rel=2e-3)


def test_cds_at_market_spread_is_near_zero(md):
    spread = md.credit_curves["ACME"][5.0]
    cds = make("CreditDefaultSwap", reference="ACME", coupon=spread)
    res = cds.price(md)
    assert res.components["par_spread"] == pytest.approx(spread, rel=0.02)
    assert abs(res.npv) < 1_000_000 * 0.001
    seller = make("CreditDefaultSwap", reference="ACME", coupon=0.005, is_buyer=False)
    assert seller.price(md).npv < 0 < make("CreditDefaultSwap", reference="ACME", coupon=0.005).price(md).npv


def test_fx_put_call_parity(md):
    call = make("FXOption", pair="EURUSD", strike=1.10, is_call=True)
    put = make("FXOption", pair="EURUSD", strike=1.10, is_call=False)
    fwd = call.price(md).components["forward"]
    t = (MAT - VALUATION_DATE).days / 365.25
    df = np.exp(-curve_value(md.discount_curve, t) * t)
    assert call.price(md).npv - put.price(md).npv == pytest.approx(1_000_000 * df * (fwd - 1.10), rel=1e-6)


def test_barrier_cheaper_than_vanilla_and_in_out_parity(md):
    kw = dict(pair="EURUSD", strike=1.10, barrier=1.30)
    vanilla = make("FXOption", **kw).price(md).npv
    up_out = make("FXBarrierOption", barrier_type="UpOut", **kw).price(md).npv
    up_in = make("FXBarrierOption", barrier_type="UpIn", **kw).price(md).npv
    assert 0 < up_out < vanilla
    assert up_out + up_in == pytest.approx(vanilla, rel=1e-3)   # QuantLib day-count rounding


def test_atm_forwards_start_at_zero(md):
    for name, kw in [("EquityForward", {"ticker": "SPX"}), ("CommodityForward", {"commodity": "WTI"}),
                     ("CommoditySwap", {"commodity": "WTI"}), ("NonDeliverableForward", {"pair": "USDJPY"})]:
        assert make(name, **kw).price(md).npv == pytest.approx(0.0, abs=1e-6), name


def test_cash_equity_fixes_quantity(md):
    stock = make("CommonStock", ticker="AAPL")
    assert stock.price(md).npv == pytest.approx(1_000_000)
    md.equity_prices["AAPL"] *= 1.1
    assert stock.price(md).npv == pytest.approx(1_100_000)
