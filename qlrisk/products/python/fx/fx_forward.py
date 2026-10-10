"""
QLRisk - FXForward v1.2.0
========================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from datetime import date
from typing import Dict, Any, Optional
import numpy as np

from ...base import curve_value
from ...base import (
    BaseProduct, ProductType, AssetClass, Currency,
    DayCountConvention,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class FXForward(BaseProduct):
    """FX Forward - agreement to exchange currencies at future date."""
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        settlement_date: date,
        base_currency: Currency,
        quote_currency: Currency,
        base_notional: float,
        forward_rate: float,
        counterparty_id: str,
        is_buy_base: bool = True,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.FX_FORWARD,
            asset_class=AssetClass.FX,
            trade_date=trade_date,
            effective_date=trade_date,
            maturity_date=settlement_date,
            notional=base_notional,
            currency=base_currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.base_notional = base_notional
        self.quote_notional = base_notional * forward_rate
        self.forward_rate = forward_rate
        self.is_buy_base = is_buy_base
    
    def price(self, market_data: MarketData) -> PricingResult:
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.quote_currency.value)
        
        pair = f"{self.base_currency.value}{self.quote_currency.value}"
        spot = market_data.fx_spots.get(pair, self.forward_rate)
        
        remaining = self.get_remaining_maturity(valuation_date)
        discount_curve = market_data.discount_curve
        df = np.exp(-curve_value(discount_curve, remaining, 0.05) * remaining)
        
        fair_forward = spot * np.exp((curve_value(discount_curve, remaining, 0.05) - curve_value(discount_curve, remaining, 0.05)) * remaining)
        
        if self.is_buy_base:
            npv = self.base_notional * (fair_forward - self.forward_rate) * df
        else:
            npv = self.base_notional * (self.forward_rate - fair_forward) * df
        
        return PricingResult(
            npv=npv,
            currency=self.quote_currency.value,
            components={"spot": spot, "forward_rate": self.forward_rate, "fair_forward": fair_forward},
            greeks={"fx_delta": self.base_notional * df * (1 if self.is_buy_base else -1)},
            metadata={"product_type": self.product_type.value}
        )
    
    def calculate_ccr_exposure(self, market_data: MarketData, time_horizon: float = 5.0, num_scenarios: int = 10000, confidence_level: float = 0.95) -> CCRExposureProfile:
        result = self.price(market_data)
        npv = result.npv
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining) if remaining > 0 else 0.1
        time_grid = list(np.linspace(0, max(0.1, horizon), 10))
        
        np.random.seed(42)
        fx_vol = 0.10
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            if t == 0:
                ee_profile.append(max(0, npv))
                pfe_profile.append(max(0, npv))
                continue
            
            shocks = np.random.normal(0, fx_vol * np.sqrt(t), num_scenarios)
            time_factor = max(0, 1 - t/remaining) if remaining > 0 else 0
            npv_sims = npv + self.base_notional * shocks * time_factor
            exposures = np.maximum(0, npv_sims)
            ee_profile.append(np.mean(exposures))
            pfe_profile.append(np.percentile(exposures, confidence_level * 100))
        
        return CCRExposureProfile(time_grid=time_grid, expected_exposure=ee_profile, potential_future_exposure=pfe_profile, effective_ee=ee_profile, peak_exposure=max(pfe_profile), epe=np.mean(ee_profile), effective_epe=np.mean(ee_profile), cva=0.0)
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        result = self.price(market_data)
        rc = max(0, result.npv)
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        sf = SACCRParameters.get_supervisory_factor(AssetClass.FX)
        mf = SACCRParameters.calculate_maturity_factor(remaining)
        delta = 1.0 if self.is_buy_base else -1.0
        pfe_addon = sf * abs(delta) * self.base_notional * mf
        return SACCRExposure(replacement_cost=rc, pfe_add_on=pfe_addon, ead=SACCRParameters.ALPHA * (rc + pfe_addon), asset_class=AssetClass.FX)


__all__ = ["FXForward"]
