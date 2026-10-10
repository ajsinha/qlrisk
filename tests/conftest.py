"""
Shared fixtures for the QLRisk test suite.

Includes two small analytic products so sensitivities can be checked
against closed-form answers independently of the product library.
"""

from datetime import date, timedelta

import numpy as np
import pytest
from scipy.stats import norm

from qlrisk.data import create_sample_market_data
from qlrisk.products.base import (
    AssetClass, BaseProduct, Currency, MarketData, PricingResult, ProductType, curve_value,
)

VALUATION_DATE = date(2026, 10, 9)


class AnalyticZeroCouponBond(BaseProduct):
    """PV = N * exp(-r(T) * T) on the discount curve."""
    
    def __init__(self, trade_id: str, maturity_years: float, notional: float = 1_000_000.0,
                 valuation_date: date = VALUATION_DATE):
        super().__init__(
            trade_id, ProductType.TREASURY_BOND, AssetClass.FIXED_INCOME, valuation_date, valuation_date,
            valuation_date + timedelta(days=round(maturity_years * 365.25)), notional, Currency.USD, "TEST",
        )
        self.maturity_years = maturity_years
    
    def time_to_maturity(self, market_data: MarketData) -> float:
        return (self.maturity_date - market_data.valuation_date).days / 365.25
    
    def price(self, market_data: MarketData) -> PricingResult:
        t = self.time_to_maturity(market_data)
        r = curve_value(market_data.discount_curve, t)
        return PricingResult(npv=self.notional * np.exp(-r * t), currency="USD")
    
    def calculate_ccr_exposure(self, *args, **kwargs):
        raise NotImplementedError
    
    def calculate_saccr(self, *args, **kwargs):
        raise NotImplementedError


class AnalyticEquityCall(BaseProduct):
    """Black-Scholes call on equity_prices[ticker] with flat vol volatility_surfaces['eq_flat_vol']."""
    
    def __init__(self, trade_id: str, ticker: str, strike: float, expiry_years: float,
                 quantity: float = 1_000.0, valuation_date: date = VALUATION_DATE):
        super().__init__(
            trade_id, ProductType.EQUITY_OPTION, AssetClass.EQUITY, valuation_date, valuation_date,
            valuation_date + timedelta(days=round(expiry_years * 365.25)), quantity, Currency.USD, "TEST",
        )
        self.ticker, self.strike, self.quantity = ticker, strike, quantity
    
    def inputs(self, market_data: MarketData):
        t = (self.maturity_date - market_data.valuation_date).days / 365.25
        s = market_data.equity_prices[self.ticker]
        vol = market_data.volatility_surfaces["eq_flat_vol"]
        r = curve_value(market_data.discount_curve, t)
        return s, t, r, vol
    
    def price(self, market_data: MarketData) -> PricingResult:
        s, t, r, vol = self.inputs(market_data)
        d1 = (np.log(s / self.strike) + (r + 0.5 * vol ** 2) * t) / (vol * np.sqrt(t))
        d2 = d1 - vol * np.sqrt(t)
        call = s * norm.cdf(d1) - self.strike * np.exp(-r * t) * norm.cdf(d2)
        return PricingResult(npv=self.quantity * call, currency="USD")
    
    def analytic_greeks(self, market_data: MarketData):
        s, t, r, vol = self.inputs(market_data)
        d1 = (np.log(s / self.strike) + (r + 0.5 * vol ** 2) * t) / (vol * np.sqrt(t))
        return {
            "delta": self.quantity * norm.cdf(d1),
            "gamma": self.quantity * norm.pdf(d1) / (s * vol * np.sqrt(t)),
            "vega": self.quantity * s * norm.pdf(d1) * np.sqrt(t),
        }
    
    def calculate_ccr_exposure(self, *args, **kwargs):
        raise NotImplementedError
    
    def calculate_saccr(self, *args, **kwargs):
        raise NotImplementedError


@pytest.fixture
def md() -> MarketData:
    """Sample multi-asset market data plus a flat equity vol for the analytic call."""
    data = create_sample_market_data(VALUATION_DATE)
    data.volatility_surfaces["eq_flat_vol"] = 0.25
    return data


@pytest.fixture
def simple_md() -> MarketData:
    """Small, hand-built market data for exact assertions."""
    return MarketData(
        valuation_date=VALUATION_DATE,
        discount_curve={1.0: 0.04, 5.0: 0.05, 10.0: 0.06},
        forward_curves={"SOFR": {1.0: 0.041, 5.0: 0.051}},
        fx_spots={"EURUSD": 1.10, "USDJPY": 150.0},
        volatility_surfaces={"swaption_vol": 0.20, "cap_vol": {1.0: 0.22, 2.0: 0.21},
                             "eq_vol": {1.0: {90.0: 0.25, 100.0: 0.20}}},
        credit_curves={"ACME": {5.0: 0.012}},
        equity_prices={"AAPL": 190.0},
    )
