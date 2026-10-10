"""
QLRisk - Overnight Index Swap v1.2.0
===================================================

OIS implementation for CCR calculation.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from ...base import curve_value
from ...base import (
    BaseProduct, ProductType, AssetClass, Currency, FloatingRateIndex,
    DayCountConvention, PaymentFrequency,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class OvernightIndexSwap(BaseProduct):
    """Overnight Index Swap - floating leg tied to overnight rate."""
    
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
        overnight_index: FloatingRateIndex = FloatingRateIndex.SOFR,
        is_payer: bool = True,
        payment_frequency: PaymentFrequency = PaymentFrequency.ANNUAL,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.OIS,
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
        self.overnight_index = overnight_index
        self.is_payer = is_payer
        self.payment_frequency = payment_frequency
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the OIS."""
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        discount_curve = market_data.discount_curve
        remaining_maturity = self.get_remaining_maturity(valuation_date)
        
        df = np.exp(-curve_value(discount_curve, remaining_maturity, 0.05) * remaining_maturity)
        
        # OIS fixed leg PV
        fixed_pv = self.notional * self.fixed_rate * remaining_maturity * df
        
        # OIS float leg approximation (at par initially)
        ois_rate = curve_value(discount_curve, remaining_maturity, 0.05)
        float_pv = self.notional * ois_rate * remaining_maturity * df
        
        if self.is_payer:
            npv = float_pv - fixed_pv
        else:
            npv = fixed_pv - float_pv
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "fixed_leg_pv": fixed_pv,
                "float_leg_pv": float_pv,
                "ois_rate": ois_rate,
            },
            greeks={
                "dv01": self.notional * remaining_maturity * df * 0.0001,
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
        npv = result.npv
        dv01 = result.greeks.get("dv01", self.notional * 0.0001)
        
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining)
        
        time_grid = list(np.linspace(0, horizon, 10))
        
        ee_profile = []
        pfe_profile = []
        
        vol = 0.01
        np.random.seed(42)
        
        for t in time_grid:
            if t == 0:
                ee_profile.append(max(0, npv))
                pfe_profile.append(max(0, npv))
                continue
            
            shocks = np.random.normal(0, vol * np.sqrt(t), num_scenarios)
            npv_sims = npv + dv01 * 10000 * shocks
            time_factor = max(0, 1 - t / remaining)
            exposures = np.maximum(0, npv_sims * time_factor)
            
            ee_profile.append(np.mean(exposures))
            pfe_profile.append(np.percentile(exposures, confidence_level * 100))
        
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=ee_profile,
            peak_exposure=max(pfe_profile),
            epe=np.mean(ee_profile),
            effective_epe=np.mean(ee_profile),
            cva=0.0
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """Calculate SA-CCR."""
        result = self.price(market_data)
        rc = max(0, result.npv)
        
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining)
        sd = SACCRParameters.supervisory_duration(0, remaining)
        
        effective_notional = self.notional * sd
        delta = 1.0 if self.is_payer else -1.0
        pfe_addon = sf * abs(delta) * effective_notional * mf
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=SACCRParameters.ALPHA * (rc + pfe_addon),
            asset_class=AssetClass.INTEREST_RATE
        )


__all__ = ["OvernightIndexSwap"]
