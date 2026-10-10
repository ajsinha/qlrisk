"""
QLRisk - Collateral Swap v2.0.1
==============================================

Collateral Swap product implementation for Securities Financing Transactions.

A Collateral Swap is a transaction where two parties exchange collateral,
typically to transform one type of collateral into another more suitable
for regulatory or operational purposes.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Any, List, Optional
from enum import Enum
import math
import numpy as np

from ...base import curve_value
from ...base import (
    BaseProduct, ProductType, AssetClass, Currency,
    DayCountConvention, PaymentFrequency,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class CollateralQuality(Enum):
    """Quality tier of collateral."""
    HQLA_LEVEL_1 = "hqla_1"      # Cash, G-Secs (0% haircut)
    HQLA_LEVEL_2A = "hqla_2a"    # GSE, Covered bonds (15% haircut)
    HQLA_LEVEL_2B = "hqla_2b"    # Corporate bonds, equities (25-50% haircut)
    NON_HQLA = "non_hqla"        # Other eligible (50%+ haircut)


@dataclass
class CollateralLeg:
    """One leg of the collateral swap."""
    collateral_type: str
    quality: CollateralQuality
    market_value: float
    haircut: float
    issuer: str = ""
    security_id: str = ""
    currency: str = "USD"
    maturity: Optional[date] = None
    volatility: float = 0.05


class CollateralSwap(BaseProduct):
    """
    Collateral Swap Transaction.
    
    A transaction where two parties exchange collateral:
    - Party A delivers Collateral X
    - Party B delivers Collateral Y
    - At maturity, collateral is returned
    - A fee may be paid based on collateral quality differential
    
    Use Cases:
    - Collateral upgrade/downgrade trades
    - LCR/NSFR optimization
    - Regulatory collateral transformation
    - Central clearing collateral management
    
    CCR Characteristics:
    - Exposure from value changes in exchanged collateral
    - Asymmetric risk if collateral types differ
    - Important for liquidity regulations (LCR, NSFR)
    """
    
    # LCR haircuts by quality
    LCR_HAIRCUTS = {
        CollateralQuality.HQLA_LEVEL_1: 0.0,
        CollateralQuality.HQLA_LEVEL_2A: 0.15,
        CollateralQuality.HQLA_LEVEL_2B: 0.25,
        CollateralQuality.NON_HQLA: 0.50,
    }
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,  # Reference notional for the swap
        currency: Currency,
        counterparty_id: str,
        # Collateral Swap specific
        receive_leg: Optional[CollateralLeg] = None,
        deliver_leg: Optional[CollateralLeg] = None,
        fee_rate: float = 0.0,  # Annual fee (positive = we pay)
        fee_payment_frequency: PaymentFrequency = PaymentFrequency.QUARTERLY,
        initial_margin_pct: float = 0.02,  # 2% initial margin
        variation_margin: bool = True,
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.REPO,  # Classify as SFT
            asset_class=AssetClass.INTEREST_RATE,  # Default
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        # Default legs if not specified
        self.receive_leg = receive_leg or CollateralLeg(
            collateral_type="government_bond",
            quality=CollateralQuality.HQLA_LEVEL_1,
            market_value=notional,
            haircut=0.02
        )
        self.deliver_leg = deliver_leg or CollateralLeg(
            collateral_type="corporate_bond",
            quality=CollateralQuality.HQLA_LEVEL_2B,
            market_value=notional,
            haircut=0.08
        )
        
        self.fee_rate = fee_rate
        self.fee_payment_frequency = fee_payment_frequency
        self.initial_margin_pct = initial_margin_pct
        self.variation_margin = variation_margin
        self.day_count = day_count
        
        # Determine direction based on quality upgrade/downgrade
        self.is_upgrade = (
            self.receive_leg.quality.value < self.deliver_leg.quality.value
        )
    
    def _calculate_lcr_impact(self) -> Dict[str, float]:
        """Calculate LCR impact of the swap."""
        receive_lcr_value = self.receive_leg.market_value * (
            1 - self.LCR_HAIRCUTS.get(self.receive_leg.quality, 0.5)
        )
        deliver_lcr_value = self.deliver_leg.market_value * (
            1 - self.LCR_HAIRCUTS.get(self.deliver_leg.quality, 0.5)
        )
        
        return {
            "receive_lcr_value": receive_lcr_value,
            "deliver_lcr_value": deliver_lcr_value,
            "lcr_improvement": receive_lcr_value - deliver_lcr_value
        }
    
    def price(self, market_data: MarketData) -> PricingResult:
        """
        Price the Collateral Swap.
        
        Value = (Receive Leg Value - Deliver Leg Value) - PV(Fees)
        """
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        remaining = self.get_remaining_maturity(valuation_date)
        elapsed = year_fraction(self.effective_date, valuation_date, self.day_count)
        
        # Get discount factor
        discount_curve = market_data.discount_curve
        df = math.exp(-curve_value(discount_curve, remaining, 0.05) * remaining)
        
        # Calculate current collateral values
        # Receive leg (what we receive)
        receive_value = self.receive_leg.market_value
        if self.receive_leg.security_id:
            receive_price = market_data.bond_prices.get(
                self.receive_leg.security_id,
                100.0
            )
            receive_value = self.receive_leg.market_value * receive_price / 100
        
        # Deliver leg (what we deliver)
        deliver_value = self.deliver_leg.market_value
        if self.deliver_leg.security_id:
            deliver_price = market_data.bond_prices.get(
                self.deliver_leg.security_id,
                100.0
            )
            deliver_value = self.deliver_leg.market_value * deliver_price / 100
        
        # Apply haircuts for adjusted values
        adjusted_receive = receive_value * (1 - self.receive_leg.haircut)
        adjusted_deliver = deliver_value * (1 - self.deliver_leg.haircut)
        
        # Net value difference
        net_value = adjusted_receive - adjusted_deliver
        
        # Calculate fees
        accrued_fee = self.fee_rate * self.notional * elapsed
        future_fees = self.fee_rate * self.notional * remaining
        
        # NPV
        npv = net_value - accrued_fee - future_fees * df
        
        # Calculate LCR impact
        lcr_impact = self._calculate_lcr_impact()
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "receive_leg_value": receive_value,
                "deliver_leg_value": deliver_value,
                "adjusted_receive": adjusted_receive,
                "adjusted_deliver": adjusted_deliver,
                "net_value": net_value,
                "accrued_fee": accrued_fee,
                "remaining_maturity": remaining,
                **lcr_impact
            },
            greeks={
                "receive_delta": 1 - self.receive_leg.haircut,
                "deliver_delta": -(1 - self.deliver_leg.haircut),
                "fee_sensitivity": -self.notional * remaining
            },
            metadata={
                "product_type": "collateral_swap",
                "is_upgrade": self.is_upgrade,
                "receive_quality": self.receive_leg.quality.value,
                "deliver_quality": self.deliver_leg.quality.value,
                "fee_rate": self.fee_rate
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 1.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure profile."""
        result = self.price(market_data)
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        
        if remaining <= 0:
            return CCRExposureProfile(
                time_grid=[0],
                expected_exposure=[0],
                potential_future_exposure=[0],
                effective_ee=[0],
                peak_exposure=0,
                epe=0,
                effective_epe=0,
                cva=0.0
            )
        
        horizon = min(time_horizon, remaining)
        num_steps = max(4, int(horizon * 12))
        time_grid = list(np.linspace(0, horizon, num_steps))
        
        # Volatilities
        receive_vol = self.receive_leg.volatility
        deliver_vol = self.deliver_leg.volatility
        correlation = 0.7  # Typically high correlation between collateral types
        
        receive_value = result.components.get("receive_leg_value", self.receive_leg.market_value)
        deliver_value = result.components.get("deliver_leg_value", self.deliver_leg.market_value)
        
        dt = horizon / num_steps
        
        # Correlated paths
        z1 = np.random.standard_normal((num_scenarios, num_steps))
        z2 = correlation * z1 + np.sqrt(1 - correlation**2) * np.random.standard_normal((num_scenarios, num_steps))
        
        receive_paths = np.zeros((num_scenarios, num_steps + 1))
        deliver_paths = np.zeros((num_scenarios, num_steps + 1))
        receive_paths[:, 0] = receive_value
        deliver_paths[:, 0] = deliver_value
        
        for i in range(num_steps):
            receive_paths[:, i+1] = receive_paths[:, i] * np.exp(-0.5 * receive_vol**2 * dt + receive_vol * np.sqrt(dt) * z1[:, i])
            deliver_paths[:, i+1] = deliver_paths[:, i] * np.exp(-0.5 * deliver_vol**2 * dt + deliver_vol * np.sqrt(dt) * z2[:, i])
        
        ee_profile = []
        pfe_profile = []
        
        for i, t in enumerate(time_grid):
            adj_receive = receive_paths[:, i] * (1 - self.receive_leg.haircut)
            adj_deliver = deliver_paths[:, i] * (1 - self.deliver_leg.haircut)
            
            exposures = np.maximum(0, adj_receive - adj_deliver)
            ee_profile.append(float(np.mean(exposures)))
            pfe_profile.append(float(np.percentile(exposures, confidence_level * 100)))
        
        effective_ee = []
        max_ee = 0
        for ee in ee_profile:
            max_ee = max(max_ee, ee)
            effective_ee.append(max_ee)
        
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=effective_ee,
            peak_exposure=max(pfe_profile),
            epe=np.mean(ee_profile),
            effective_epe=np.mean(effective_ee),
            cva=0.0
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """Calculate SA-CCR EAD for Collateral Swap."""
        result = self.price(market_data)
        
        receive_value = result.components.get("receive_leg_value", self.receive_leg.market_value)
        deliver_value = result.components.get("deliver_leg_value", self.deliver_leg.market_value)
        
        # Net exposure
        rc = max(0, result.components.get("net_value", 0))
        
        # PFE based on the larger leg with volatility adjustment
        larger_value = max(receive_value, deliver_value)
        avg_vol = (self.receive_leg.volatility + self.deliver_leg.volatility) / 2
        pfe_addon = larger_value * avg_vol * 0.5  # Simplified
        
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.INTEREST_RATE,
            details={
                "receive_leg_value": receive_value,
                "deliver_leg_value": deliver_value,
                "is_upgrade": self.is_upgrade,
                "receive_haircut": self.receive_leg.haircut,
                "deliver_haircut": self.deliver_leg.haircut
            }
        )


__all__ = ["CollateralSwap", "CollateralQuality", "CollateralLeg"]
