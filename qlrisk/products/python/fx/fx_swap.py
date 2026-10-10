"""
QLRisk - FXSwap v1.2.0
=====================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from datetime import date
from typing import Dict, Any, Optional
import numpy as np

from ...base import (
    BaseProduct, ProductType, AssetClass, Currency,
    DayCountConvention,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class FXSwap(BaseProduct):
    """FX Swap - spot + forward transaction."""
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        near_date: date,
        far_date: date,
        base_currency: Currency,
        quote_currency: Currency,
        base_notional: float,
        near_rate: float,
        far_rate: float,
        counterparty_id: str,
        buy_base_near: bool = True,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.FX_SWAP,
            asset_class=AssetClass.FX,
            trade_date=trade_date,
            effective_date=near_date,
            maturity_date=far_date,
            notional=base_notional,
            currency=base_currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.near_date = near_date
        self.far_date = far_date
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.base_notional = base_notional
        self.near_rate = near_rate
        self.far_rate = far_rate
        self.buy_base_near = buy_base_near
    
    def price(self, market_data: MarketData) -> PricingResult:
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.quote_currency.value)
        
        pair = f"{self.base_currency.value}{self.quote_currency.value}"
        spot = market_data.fx_spots.get(pair, self.near_rate)
        
        swap_points = self.far_rate - self.near_rate
        npv = self.base_notional * swap_points * 0.5
        
        if not self.buy_base_near:
            npv = -npv
        
        return PricingResult(
            npv=npv,
            currency=self.quote_currency.value,
            components={"swap_points": swap_points * 10000, "near_rate": self.near_rate, "far_rate": self.far_rate},
            greeks={"fx_delta": self.base_notional},
            metadata={"product_type": self.product_type.value}
        )
    
    def calculate_ccr_exposure(self, market_data: MarketData, time_horizon: float = 5.0, num_scenarios: int = 10000, confidence_level: float = 0.95) -> CCRExposureProfile:
        result = self.price(market_data)
        npv = result.npv
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining) if remaining > 0 else 0.1
        time_grid = list(np.linspace(0, max(0.1, horizon), 10))
        ee_profile = [max(0, npv * (1 - t/remaining)) if remaining > 0 else 0 for t in time_grid]
        pfe_profile = [e * 1.3 for e in ee_profile]
        return CCRExposureProfile(time_grid=time_grid, expected_exposure=ee_profile, potential_future_exposure=pfe_profile, effective_ee=ee_profile, peak_exposure=max(pfe_profile) if pfe_profile else 0, epe=np.mean(ee_profile), effective_epe=np.mean(ee_profile), cva=0.0)
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        result = self.price(market_data)
        rc = max(0, result.npv)
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        sf = SACCRParameters.get_supervisory_factor(AssetClass.FX)
        mf = SACCRParameters.calculate_maturity_factor(remaining)
        pfe_addon = sf * self.base_notional * mf
        return SACCRExposure(replacement_cost=rc, pfe_add_on=pfe_addon, ead=SACCRParameters.ALPHA * (rc + pfe_addon), asset_class=AssetClass.FX)


__all__ = ["FXSwap"]
