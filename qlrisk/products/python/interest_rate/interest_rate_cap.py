"""
QLRisk - Interest Rate Cap v1.2.0
================================================

Interest Rate Cap implementation for CCR calculation.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from datetime import date
from typing import Dict, Any, List, Optional
import numpy as np
from scipy.stats import norm

from ...base import (
    BaseProduct, ProductType, AssetClass, Currency, FloatingRateIndex,
    DayCountConvention, PaymentFrequency,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class InterestRateCap(BaseProduct):
    """Interest Rate Cap - series of caplets."""
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,
        currency: Currency,
        counterparty_id: str,
        strike: float,
        floating_index: FloatingRateIndex = FloatingRateIndex.SOFR,
        frequency: PaymentFrequency = PaymentFrequency.QUARTERLY,
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        is_long: bool = True,
        volatility: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.CAP,
            asset_class=AssetClass.INTEREST_RATE,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.strike = strike
        self.floating_index = floating_index
        self.frequency = frequency
        self.day_count = day_count
        self.is_long = is_long
        self.volatility = volatility
    
    def _black_caplet(self, forward: float, strike: float, vol: float, tau: float, df: float, notional: float) -> float:
        """Price single caplet using Black's model."""
        if tau <= 0 or vol <= 0:
            return max(0, forward - strike) * notional * tau * df
        
        d1 = (np.log(forward / strike) + 0.5 * vol**2 * tau) / (vol * np.sqrt(tau))
        d2 = d1 - vol * np.sqrt(tau)
        
        return notional * tau * df * (forward * norm.cdf(d1) - strike * norm.cdf(d2))
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the cap."""
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        discount_curve = market_data.discount_curve
        vol = self.volatility or market_data.volatility_surfaces.get("cap_vol", 0.20)
        if isinstance(vol, dict):
            vol = 0.20
        
        # Generate caplet schedule
        freq_months = {
            PaymentFrequency.MONTHLY: 1,
            PaymentFrequency.QUARTERLY: 3,
            PaymentFrequency.SEMI_ANNUAL: 6,
            PaymentFrequency.ANNUAL: 12,
        }
        months = freq_months.get(self.frequency, 3)
        
        total_premium = 0.0
        total_vega = 0.0
        
        current = max(self.effective_date, valuation_date)
        
        while current < self.maturity_date:
            next_date = date(
                current.year + (current.month + months - 1) // 12,
                (current.month + months - 1) % 12 + 1,
                min(current.day, 28)
            )
            next_date = min(next_date, self.maturity_date)
            
            if next_date > valuation_date:
                tau_fix = year_fraction(valuation_date, current, DayCountConvention.ACT_365)
                tau_pay = year_fraction(valuation_date, next_date, DayCountConvention.ACT_365)
                tau_period = year_fraction(current, next_date, self.day_count)
                
                df = np.exp(-discount_curve.get(tau_pay, 0.05) * tau_pay)
                fwd = discount_curve.get(tau_pay, 0.05)
                
                caplet = self._black_caplet(fwd, self.strike, vol, max(tau_fix, 0.01), df, self.notional)
                total_premium += caplet
                
                # Vega
                if tau_fix > 0:
                    total_vega += caplet * np.sqrt(tau_fix) / vol * 0.01
            
            current = next_date
        
        if not self.is_long:
            total_premium = -total_premium
            total_vega = -total_vega
        
        return PricingResult(
            npv=total_premium,
            currency=self.currency.value,
            components={
                "premium": total_premium,
                "strike": self.strike,
                "volatility": vol,
            },
            greeks={
                "vega": total_vega,
            },
            metadata={"product_type": self.product_type.value}
        )
    
    def calculate_ccr_exposure(
        self, market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure."""
        result = self.price(market_data)
        npv = max(0, result.npv) if self.is_long else 0
        
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining)
        
        time_grid = list(np.linspace(0, horizon, 10))
        ee_profile = [npv * np.sqrt(max(0, 1 - t/remaining)) for t in time_grid]
        pfe_profile = [e * 1.3 for e in ee_profile]
        
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=ee_profile,
            peak_exposure=max(pfe_profile) if pfe_profile else 0,
            epe=np.mean(ee_profile),
            effective_epe=np.mean(ee_profile),
            cva=0.0
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """Calculate SA-CCR."""
        result = self.price(market_data)
        rc = max(0, result.npv) if self.is_long else 0
        
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining)
        sd = SACCRParameters.supervisory_duration(0, remaining)
        
        vol = self.volatility or 0.50
        delta = SACCRParameters.calculate_option_delta(True, self.strike, self.strike, remaining, vol)
        
        pfe_addon = sf * abs(delta) * self.notional * sd * mf
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=SACCRParameters.ALPHA * (rc + pfe_addon),
            asset_class=AssetClass.INTEREST_RATE
        )


__all__ = ["InterestRateCap"]
