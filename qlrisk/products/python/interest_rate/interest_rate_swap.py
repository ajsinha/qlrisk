"""
QLRisk - Interest Rate Swap v1.2.0
=================================================

Interest Rate Swap (IRS) implementation for CCR calculation.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy.stats import norm

from ...base import curve_value
from ...base import (
    BaseProduct, ProductType, AssetClass, Currency, FloatingRateIndex,
    DayCountConvention, PaymentFrequency, BusinessDayConvention,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction, discount_factor
)


@dataclass
class IRSLeg:
    """Specification of a single swap leg."""
    is_fixed: bool
    rate: Optional[float] = None
    index: Optional[FloatingRateIndex] = None
    frequency: PaymentFrequency = PaymentFrequency.QUARTERLY
    day_count: DayCountConvention = DayCountConvention.ACT_360
    notional: float = 0.0
    currency: Currency = Currency.USD


class InterestRateSwap(BaseProduct):
    """
    Interest Rate Swap product.
    
    Exchange of fixed-rate for floating-rate interest payments.
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,
        currency: Currency,
        counterparty_id: str,
        fixed_rate: float,
        floating_index: FloatingRateIndex = FloatingRateIndex.SOFR,
        is_payer: bool = True,
        fixed_frequency: PaymentFrequency = PaymentFrequency.SEMI_ANNUAL,
        float_frequency: PaymentFrequency = PaymentFrequency.QUARTERLY,
        fixed_day_count: DayCountConvention = DayCountConvention.THIRTY_360,
        float_day_count: DayCountConvention = DayCountConvention.ACT_360,
        spread: float = 0.0,
        amortization_schedule: Optional[List[Tuple[date, float]]] = None,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.IRS,
            asset_class=AssetClass.INTEREST_RATE,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.fixed_rate = fixed_rate
        self.floating_index = floating_index
        self.is_payer = is_payer
        self.fixed_frequency = fixed_frequency
        self.float_frequency = float_frequency
        self.fixed_day_count = fixed_day_count
        self.float_day_count = float_day_count
        self.spread = spread
        self.amortization_schedule = amortization_schedule
    
    def generate_schedule(self, frequency: PaymentFrequency) -> List[Tuple[date, date]]:
        """Generate payment schedule."""
        schedule = []
        current_date = self.effective_date
        
        freq_months = {
            PaymentFrequency.MONTHLY: 1,
            PaymentFrequency.QUARTERLY: 3,
            PaymentFrequency.SEMI_ANNUAL: 6,
            PaymentFrequency.ANNUAL: 12,
        }
        
        months = freq_months.get(frequency, 3)
        
        while current_date < self.maturity_date:
            next_date = date(
                current_date.year + (current_date.month + months - 1) // 12,
                (current_date.month + months - 1) % 12 + 1,
                min(current_date.day, 28)
            )
            next_date = min(next_date, self.maturity_date)
            schedule.append((current_date, next_date))
            current_date = next_date
            
        return schedule
    
    def get_notional_at_date(self, as_of_date: date) -> float:
        """Get notional considering amortization."""
        if not self.amortization_schedule:
            return self.notional
        
        current_notional = self.notional
        for amort_date, amort_amount in sorted(self.amortization_schedule):
            if as_of_date >= amort_date:
                current_notional -= amort_amount
        
        return max(0, current_notional)
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the interest rate swap."""
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        discount_curve = market_data.discount_curve
        forward_curve = market_data.forward_curves.get(
            self.floating_index.value if hasattr(self.floating_index, 'value') else str(self.floating_index),
            discount_curve
        )
        
        # Price fixed leg
        fixed_schedule = self.generate_schedule(self.fixed_frequency)
        fixed_pv = 0.0
        fixed_dv01 = 0.0
        
        for start, end in fixed_schedule:
            if end <= valuation_date:
                continue
            
            notional = self.get_notional_at_date(start)
            tau = year_fraction(start, end, self.fixed_day_count)
            t = year_fraction(valuation_date, end, DayCountConvention.ACT_365)
            
            df = np.exp(-curve_value(discount_curve, t, 0.05) * t)
            
            fixed_pv += notional * self.fixed_rate * tau * df
            fixed_dv01 += notional * tau * df * 0.0001
        
        # Price floating leg
        float_schedule = self.generate_schedule(self.float_frequency)
        float_pv = 0.0
        
        for start, end in float_schedule:
            if end <= valuation_date:
                continue
            
            notional = self.get_notional_at_date(start)
            tau = year_fraction(start, end, self.float_day_count)
            
            t_start = year_fraction(valuation_date, start, DayCountConvention.ACT_365)
            t_end = year_fraction(valuation_date, end, DayCountConvention.ACT_365)
            
            df_start = np.exp(-curve_value(forward_curve, t_start, 0.05) * t_start) if t_start > 0 else 1.0
            df_end = np.exp(-curve_value(forward_curve, t_end, 0.05) * t_end)
            
            if t_end > t_start and t_start >= 0:
                fwd_rate = (df_start / df_end - 1) / tau
            else:
                fwd_rate = curve_value(forward_curve, t_end, 0.05)
            
            df_discount = np.exp(-curve_value(discount_curve, t_end, 0.05) * t_end)
            float_pv += notional * (fwd_rate + self.spread) * tau * df_discount
        
        if self.is_payer:
            npv = float_pv - fixed_pv
        else:
            npv = fixed_pv - float_pv
        
        annuity = sum(
            self.get_notional_at_date(start) * 
            year_fraction(start, end, self.fixed_day_count) *
            np.exp(-curve_value(discount_curve, 
                year_fraction(valuation_date, end, DayCountConvention.ACT_365), 0.05
            ) * year_fraction(valuation_date, end, DayCountConvention.ACT_365))
            for start, end in fixed_schedule
            if end > valuation_date
        )
        
        par_rate = float_pv / annuity if annuity > 0 else self.fixed_rate
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "fixed_leg_pv": fixed_pv,
                "float_leg_pv": float_pv,
                "annuity": annuity,
                "par_rate": par_rate,
            },
            greeks={
                "dv01": fixed_dv01 * (1 if self.is_payer else -1),
            },
            metadata={"product_type": self.product_type.value}
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure profile."""
        valuation_date = market_data.valuation_date
        remaining_maturity = self.get_remaining_maturity(valuation_date)
        horizon = min(time_horizon, remaining_maturity)
        
        if horizon <= 0:
            return CCRExposureProfile(
                time_grid=[0.0], expected_exposure=[0.0],
                potential_future_exposure=[0.0], effective_ee=[0.0],
                peak_exposure=0.0, epe=0.0, effective_epe=0.0, cva=0.0
            )
        
        num_steps = max(int(horizon * 4), 4)
        time_grid = np.linspace(0, horizon, num_steps + 1)
        
        current_result = self.price(market_data)
        current_npv = current_result.npv
        current_dv01 = current_result.greeks.get("dv01", self.notional * 0.0001)
        
        vol = market_data.volatility_surfaces.get("ir_vol", 0.01)
        if isinstance(vol, dict):
            vol = 0.01
        
        np.random.seed(42)
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            if t == 0:
                ee_profile.append(max(0, current_npv))
                pfe_profile.append(max(0, current_npv))
                continue
            
            rate_shocks = np.random.normal(0, vol * np.sqrt(t), num_scenarios)
            npv_changes = current_dv01 * 10000 * rate_shocks
            
            time_factor = max(0, 1 - t / remaining_maturity)
            simulated_npvs = (current_npv + npv_changes) * time_factor
            exposures = np.maximum(0, simulated_npvs)
            
            ee_profile.append(np.mean(exposures))
            pfe_profile.append(np.percentile(exposures, confidence_level * 100))
        
        effective_ee = [ee_profile[0]]
        for ee in ee_profile[1:]:
            effective_ee.append(max(ee, effective_ee[-1]))
        
        return CCRExposureProfile(
            time_grid=list(time_grid),
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=effective_ee,
            peak_exposure=max(pfe_profile),
            epe=np.mean(ee_profile),
            effective_epe=np.mean(effective_ee),
            cva=0.0
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """Calculate SA-CCR exposure."""
        result = self.price(market_data)
        rc = max(0, result.npv)
        
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining_maturity)
        sd = SACCRParameters.supervisory_duration(0, remaining_maturity)
        
        effective_notional = self.notional * sd
        delta = 1.0 if self.is_payer else -1.0
        
        pfe_addon = sf * abs(delta) * effective_notional * mf
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.INTEREST_RATE,
            hedging_set_contributions={self.currency.value: delta * effective_notional}
        )


__all__ = ["InterestRateSwap", "IRSLeg"]
