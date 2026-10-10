"""
QLRisk - Swaption v1.2.0
=======================================

Swaption implementation for CCR calculation.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from datetime import date
from typing import Dict, Any, Optional
import numpy as np
from scipy.stats import norm

from ...base import (
    BaseProduct, ProductType, AssetClass, Currency, FloatingRateIndex,
    DayCountConvention, PaymentFrequency, OptionStyle,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class Swaption(BaseProduct):
    """Swaption - option to enter into a swap."""
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        option_expiry: date,
        swap_effective: date,
        swap_maturity: date,
        notional: float,
        currency: Currency,
        counterparty_id: str,
        strike: float,
        is_payer: bool = True,
        exercise_style: OptionStyle = OptionStyle.EUROPEAN,
        floating_index: FloatingRateIndex = FloatingRateIndex.SOFR,
        is_long: bool = True,
        volatility: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.SWAPTION,
            asset_class=AssetClass.INTEREST_RATE,
            trade_date=trade_date,
            effective_date=option_expiry,
            maturity_date=swap_maturity,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.option_expiry = option_expiry
        self.swap_effective = swap_effective
        self.swap_maturity = swap_maturity
        self.strike = strike
        self.is_payer = is_payer
        self.exercise_style = exercise_style
        self.floating_index = floating_index
        self.is_long = is_long
        self.volatility = volatility
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the swaption using Black's model."""
        valuation_date = market_data.valuation_date
        
        if valuation_date >= self.option_expiry:
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        discount_curve = market_data.discount_curve
        vol = self.volatility or market_data.volatility_surfaces.get("swaption_vol", 0.20)
        if isinstance(vol, dict):
            vol = 0.20
        
        option_maturity = year_fraction(valuation_date, self.option_expiry, DayCountConvention.ACT_365)
        swap_tenor = year_fraction(self.swap_effective, self.swap_maturity, DayCountConvention.ACT_365)
        
        # Approximate forward swap rate
        t_end = year_fraction(valuation_date, self.swap_maturity, DayCountConvention.ACT_365)
        forward_rate = discount_curve.get(t_end, 0.05)
        
        # Annuity (approximate)
        annuity = swap_tenor * np.exp(-discount_curve.get(t_end/2, 0.05) * t_end/2)
        
        # Black's model
        if option_maturity > 0 and vol > 0:
            d1 = (np.log(forward_rate / self.strike) + 0.5 * vol**2 * option_maturity) / (vol * np.sqrt(option_maturity))
            d2 = d1 - vol * np.sqrt(option_maturity)
            
            if self.is_payer:
                premium = self.notional * annuity * (forward_rate * norm.cdf(d1) - self.strike * norm.cdf(d2))
            else:
                premium = self.notional * annuity * (self.strike * norm.cdf(-d2) - forward_rate * norm.cdf(-d1))
        else:
            if self.is_payer:
                premium = self.notional * annuity * max(0, forward_rate - self.strike)
            else:
                premium = self.notional * annuity * max(0, self.strike - forward_rate)
        
        if not self.is_long:
            premium = -premium
        
        # Greeks
        if option_maturity > 0 and vol > 0:
            vega = premium * np.sqrt(option_maturity) / vol * 0.01
            delta = norm.cdf(d1) if self.is_payer else -norm.cdf(-d1)
        else:
            vega = 0
            delta = 1 if self.is_payer else -1
        
        if not self.is_long:
            delta = -delta
            vega = -vega
        
        return PricingResult(
            npv=premium,
            currency=self.currency.value,
            components={
                "premium": premium,
                "forward_rate": forward_rate,
                "strike": self.strike,
                "annuity": annuity,
                "volatility": vol,
            },
            greeks={"delta": delta, "vega": vega},
            metadata={"product_type": self.product_type.value, "is_payer": self.is_payer}
        )
    
    def calculate_ccr_exposure(self, market_data: MarketData, time_horizon: float = 5.0, num_scenarios: int = 10000, confidence_level: float = 0.95) -> CCRExposureProfile:
        result = self.price(market_data)
        npv = max(0, result.npv) if self.is_long else 0
        option_mat = year_fraction(market_data.valuation_date, self.option_expiry, DayCountConvention.ACT_365)
        horizon = min(time_horizon, option_mat)
        time_grid = list(np.linspace(0, horizon, 10))
        ee_profile = [npv * np.sqrt(max(0, option_mat - t) / option_mat) if option_mat > 0 else 0 for t in time_grid]
        pfe_profile = [e * 1.5 for e in ee_profile]
        return CCRExposureProfile(time_grid=time_grid, expected_exposure=ee_profile, potential_future_exposure=pfe_profile, effective_ee=ee_profile, peak_exposure=max(pfe_profile) if pfe_profile else 0, epe=np.mean(ee_profile), effective_epe=np.mean(ee_profile), cva=0.0)
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        result = self.price(market_data)
        rc = max(0, result.npv) if self.is_long else 0
        option_mat = year_fraction(market_data.valuation_date, self.option_expiry, DayCountConvention.ACT_365)
        swap_tenor = year_fraction(self.swap_effective, self.swap_maturity, DayCountConvention.ACT_365)
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(option_mat)
        sd = SACCRParameters.supervisory_duration(option_mat, option_mat + swap_tenor)
        delta = SACCRParameters.calculate_option_delta(self.is_payer, self.strike, self.strike, option_mat, self.volatility or 0.50)
        if not self.is_long:
            delta = -delta
        pfe_addon = sf * abs(delta) * self.notional * sd * mf
        return SACCRExposure(replacement_cost=rc, pfe_add_on=pfe_addon, ead=SACCRParameters.ALPHA * (rc + pfe_addon), asset_class=AssetClass.INTEREST_RATE)


__all__ = ["Swaption"]
