"""
QLRisk - Forward Rate Agreement v1.2.0
=====================================================

FRA implementation for CCR calculation.

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


class ForwardRateAgreement(BaseProduct):
    """Forward Rate Agreement - OTC forward on interest rate."""
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        fixing_date: date,
        settlement_date: date,
        maturity_date: date,
        notional: float,
        currency: Currency,
        counterparty_id: str,
        fra_rate: float,
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        is_payer: bool = True,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.FRA,
            asset_class=AssetClass.INTEREST_RATE,
            trade_date=trade_date,
            effective_date=settlement_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.fixing_date = fixing_date
        self.settlement_date = settlement_date
        self.fra_rate = fra_rate
        self.day_count = day_count
        self.is_payer = is_payer
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the FRA."""
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        discount_curve = market_data.discount_curve
        
        t_settle = year_fraction(valuation_date, self.settlement_date, DayCountConvention.ACT_365)
        t_maturity = year_fraction(valuation_date, self.maturity_date, DayCountConvention.ACT_365)
        tau = year_fraction(self.settlement_date, self.maturity_date, self.day_count)
        
        df_settle = np.exp(-discount_curve.get(t_settle, 0.05) * t_settle)
        df_maturity = np.exp(-discount_curve.get(t_maturity, 0.05) * t_maturity)
        
        # Forward rate
        fwd_rate = (df_settle / df_maturity - 1) / tau if tau > 0 else 0
        
        # FRA settlement amount (discounted)
        settlement = self.notional * (fwd_rate - self.fra_rate) * tau / (1 + fwd_rate * tau)
        npv = settlement * df_settle
        
        if not self.is_payer:
            npv = -npv
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "forward_rate": fwd_rate,
                "fra_rate": self.fra_rate,
                "settlement": settlement,
            },
            greeks={
                "dv01": self.notional * tau * df_settle * 0.0001,
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
        
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining)
        
        time_grid = list(np.linspace(0, horizon, 5))
        ee_profile = [max(0, npv * (1 - t/remaining)) for t in time_grid]
        pfe_profile = [e * 1.5 for e in ee_profile]
        
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
        rc = max(0, result.npv)
        
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining)
        sd = SACCRParameters.supervisory_duration(
            year_fraction(market_data.valuation_date, self.settlement_date, DayCountConvention.ACT_365),
            year_fraction(market_data.valuation_date, self.maturity_date, DayCountConvention.ACT_365)
        )
        
        pfe_addon = sf * self.notional * sd * mf
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=SACCRParameters.ALPHA * (rc + pfe_addon),
            asset_class=AssetClass.INTEREST_RATE
        )


__all__ = ["ForwardRateAgreement"]
