"""
QLRisk - Basis Swap v1.2.0
=========================================

Basis Swap implementation for CCR calculation.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from datetime import date
from typing import Dict, Any, Optional
import numpy as np

from ...base import (
    BaseProduct, ProductType, AssetClass, Currency, FloatingRateIndex,
    DayCountConvention, PaymentFrequency,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class BasisSwap(BaseProduct):
    """Basis Swap - floating vs floating with different indices."""
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,
        currency: Currency,
        counterparty_id: str,
        pay_index: FloatingRateIndex = FloatingRateIndex.SOFR,
        receive_index: FloatingRateIndex = FloatingRateIndex.SOFR,
        spread: float = 0.0,
        pay_frequency: PaymentFrequency = PaymentFrequency.QUARTERLY,
        receive_frequency: PaymentFrequency = PaymentFrequency.QUARTERLY,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.BASIS_SWAP,
            asset_class=AssetClass.INTEREST_RATE,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.pay_index = pay_index
        self.receive_index = receive_index
        self.spread = spread
        self.pay_frequency = pay_frequency
        self.receive_frequency = receive_frequency
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the basis swap."""
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        discount_curve = market_data.discount_curve
        remaining = self.get_remaining_maturity(valuation_date)
        
        df = np.exp(-discount_curve.get(remaining, 0.05) * remaining)
        
        # Basis swap NPV approximately equals spread * duration * notional * df
        npv = self.spread * remaining * self.notional * df
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "spread": self.spread,
                "remaining_maturity": remaining,
            },
            greeks={"spread_dv01": self.notional * remaining * df * 0.0001},
            metadata={"product_type": self.product_type.value}
        )
    
    def calculate_ccr_exposure(self, market_data: MarketData, time_horizon: float = 5.0, num_scenarios: int = 10000, confidence_level: float = 0.95) -> CCRExposureProfile:
        result = self.price(market_data)
        npv = result.npv
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining)
        time_grid = list(np.linspace(0, horizon, 10))
        ee_profile = [max(0, npv * (1 - t/remaining)) for t in time_grid]
        pfe_profile = [e * 1.3 for e in ee_profile]
        return CCRExposureProfile(time_grid=time_grid, expected_exposure=ee_profile, potential_future_exposure=pfe_profile, effective_ee=ee_profile, peak_exposure=max(pfe_profile) if pfe_profile else 0, epe=np.mean(ee_profile), effective_epe=np.mean(ee_profile), cva=0.0)
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        result = self.price(market_data)
        rc = max(0, result.npv)
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining)
        sd = SACCRParameters.supervisory_duration(0, remaining)
        pfe_addon = sf * self.notional * sd * mf * 0.5  # Lower add-on for basis
        return SACCRExposure(replacement_cost=rc, pfe_add_on=pfe_addon, ead=SACCRParameters.ALPHA * (rc + pfe_addon), asset_class=AssetClass.INTEREST_RATE)


__all__ = ["BasisSwap"]
