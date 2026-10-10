"""
QLRisk - MBS v1.2.0
=================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from datetime import date
from typing import Dict, Any, List, Optional
import numpy as np


from ...base import curve_value
from ...base import (
    BaseProduct, ProductType, AssetClass, Currency,
    DayCountConvention, PaymentFrequency,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class MBS(BaseProduct):
    """Mortgage-Backed Securities"""
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,
        currency: Currency,
        counterparty_id: str,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.MBS,
            asset_class=AssetClass.INTEREST_RATE,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the product."""
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        remaining = self.get_remaining_maturity(valuation_date)
        discount_curve = market_data.discount_curve
        df = np.exp(-curve_value(discount_curve, remaining, 0.05) * remaining)
        
        npv = self.notional * df * 0.01
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={"remaining_maturity": remaining},
            greeks={"dv01": self.notional * remaining * 0.0001},
            metadata={"product_type": self.product_type.value}
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        result = self.price(market_data)
        npv = max(0, result.npv)
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining) if remaining > 0 else time_horizon
        time_grid = list(np.linspace(0, max(0.1, horizon), 10))
        ee_profile = [npv * max(0, 1 - t/remaining) if remaining > 0 else 0 for t in time_grid]
        pfe_profile = [e * 1.3 for e in ee_profile]
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=ee_profile,
            peak_exposure=max(pfe_profile) if pfe_profile else 0,
            epe=np.mean(ee_profile) if ee_profile else 0,
            effective_epe=np.mean(ee_profile) if ee_profile else 0,
            cva=0.0
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        result = self.price(market_data)
        rc = max(0, result.npv)
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining)
        pfe_addon = sf * self.notional * mf
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=SACCRParameters.ALPHA * (rc + pfe_addon),
            asset_class=AssetClass.INTEREST_RATE
        )


__all__ = ["MBS"]
