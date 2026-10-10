"""
QLRisk - Fixed Income Products (QuantLib Implementation) v1.2.0
===============================================================================

QuantLib-based implementations of fixed income products for CCR calculation.

Products Implemented:
- Fixed Rate Bond
- Floating Rate Bond
- Zero Coupon Bond
- Callable Bond

Requirements:
- QuantLib Python bindings: pip install QuantLib-Python

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False

from ..base import (
    BaseProduct, AssetClass, Currency,
    DayCountConvention, PaymentFrequency,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)
from ..product_types import ProductType
from .interest_rate import to_ql_date, from_ql_date, build_yield_curve, get_ql_calendar, get_ql_day_count, get_ql_frequency


# =============================================================================
# Fixed Rate Bond (QuantLib)
# =============================================================================


def bond_yield(bond, clean_price, day_count, compounding, frequency):
    """Yield from a clean price; QuantLib >= 1.34 takes a BondPrice, older versions a float."""
    try:
        return bond.bondYield(ql.BondPrice(clean_price, ql.BondPrice.Clean), day_count, compounding, frequency)
    except (AttributeError, TypeError):
        return bond.bondYield(clean_price, day_count, compounding, frequency)

class FixedRateBondQL(BaseProduct):
    """
    Fixed Rate Bond using QuantLib pricing engine.
    
    Supports government and corporate bonds with accurate
    accrued interest and yield calculations.
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        issue_date: date,
        maturity_date: date,
        face_value: float,
        coupon_rate: float,
        currency: Currency,
        counterparty_id: str,
        coupon_frequency: PaymentFrequency = PaymentFrequency.SEMI_ANNUAL,
        day_count: DayCountConvention = DayCountConvention.ACT_ACT,
        settlement_days: int = 2,
        credit_spread: float = 0.0,
        is_long: bool = True,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.GOVERNMENT_BOND,
            asset_class=AssetClass.INTEREST_RATE,
            trade_date=trade_date,
            effective_date=issue_date,
            maturity_date=maturity_date,
            notional=face_value,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.face_value = face_value
        self.coupon_rate = coupon_rate
        self.coupon_frequency = coupon_frequency
        self.day_count = day_count
        self.settlement_days = settlement_days
        self.credit_spread = credit_spread
        self.is_long = is_long
        
        self._ql_bond = None
    
    def _build_ql_bond(self):
        """Build QuantLib FixedRateBond object."""
        calendar = get_ql_calendar(self.currency)
        
        schedule = ql.Schedule(
            to_ql_date(self.effective_date),
            to_ql_date(self.maturity_date),
            ql.Period(get_ql_frequency(self.coupon_frequency)),
            calendar,
            ql.Unadjusted,
            ql.Unadjusted,
            ql.DateGeneration.Backward,
            False
        )
        
        self._ql_bond = ql.FixedRateBond(
            self.settlement_days,
            self.face_value,
            schedule,
            [self.coupon_rate],
            get_ql_day_count(self.day_count)
        )
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the bond using QuantLib."""
        if not QUANTLIB_AVAILABLE:
            raise RuntimeError("QuantLib not available")
        
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        ql.Settings.instance().evaluationDate = to_ql_date(valuation_date)
        
        # Build bond if not already built
        if self._ql_bond is None:
            self._build_ql_bond()
        
        # Build discount curve with credit spread
        risky_curve = {
            t: r + self.credit_spread 
            for t, r in market_data.discount_curve.items()
        }
        
        calendar = get_ql_calendar(self.currency)
        yield_curve = build_yield_curve(valuation_date, risky_curve, calendar)
        
        # Set pricing engine
        engine = ql.DiscountingBondEngine(yield_curve)
        self._ql_bond.setPricingEngine(engine)
        
        # Get results
        dirty_price = self._ql_bond.dirtyPrice()
        clean_price = self._ql_bond.cleanPrice()
        accrued = self._ql_bond.accruedAmount()
        
        # Yield to maturity
        ytm = bond_yield(self._ql_bond, clean_price, get_ql_day_count(self.day_count),
                         ql.Compounded, get_ql_frequency(self.coupon_frequency))
        
        # Duration and convexity
        flat_rate = ql.InterestRate(
            ytm,
            get_ql_day_count(self.day_count),
            ql.Compounded,
            get_ql_frequency(self.coupon_frequency)
        )
        
        macaulay_duration = ql.BondFunctions.duration(
            self._ql_bond,
            flat_rate,
            ql.Duration.Macaulay
        )
        
        modified_duration = ql.BondFunctions.duration(
            self._ql_bond,
            flat_rate,
            ql.Duration.Modified
        )
        
        convexity = ql.BondFunctions.convexity(self._ql_bond, flat_rate)
        
        # BPV (DV01)
        bpv = ql.BondFunctions.basisPointValue(self._ql_bond, flat_rate)
        
        # NPV
        npv = self._ql_bond.NPV()
        if not self.is_long:
            npv = -npv
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "dirty_price": dirty_price,
                "clean_price": clean_price,
                "accrued_interest": accrued,
                "price_pct": clean_price,
                "ytm": ytm,
                "macaulay_duration": macaulay_duration,
                "modified_duration": modified_duration,
                "convexity": convexity,
            },
            greeks={
                "dv01": bpv * (self.face_value / 100) * (1 if self.is_long else -1),
                "duration": modified_duration,
                "convexity": convexity,
            },
            metadata={
                "product_type": self.product_type.value,
                "pricing_engine": "QuantLib.DiscountingBond",
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure profile."""
        result = self.price(market_data)
        current_npv = result.npv
        dv01 = result.greeks.get("dv01", 0)
        
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining_maturity)
        
        rate_vol = market_data.volatility_surfaces.get("ir_vol", 0.01)
        if isinstance(rate_vol, dict):
            rate_vol = 0.01
        
        time_grid = list(np.linspace(0, horizon, 10))
        
        np.random.seed(42)
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            if t == 0:
                ee_profile.append(max(0, current_npv))
                pfe_profile.append(max(0, current_npv))
                continue
            
            rate_shocks = np.random.normal(0, rate_vol * np.sqrt(t), num_scenarios)
            npv_changes = dv01 * 10000 * rate_shocks
            
            time_factor = max(0, 1 - t / remaining_maturity) if remaining_maturity > 0 else 0
            simulated_npvs = (current_npv + npv_changes) * time_factor
            
            exposures = np.maximum(0, simulated_npvs)
            
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
        """Calculate SA-CCR exposure."""
        result = self.price(market_data)
        rc = max(0, result.npv)
        
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        duration = result.greeks.get("duration", remaining_maturity)
        
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining_maturity)
        
        effective_notional = self.face_value * duration
        delta = 1.0 if self.is_long else -1.0
        
        pfe_addon = sf * np.abs(delta) * effective_notional * mf
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.INTEREST_RATE
        )


# =============================================================================
# Floating Rate Bond (QuantLib)
# =============================================================================

class FloatingRateBondQL(BaseProduct):
    """
    Floating Rate Bond (FRN) using QuantLib pricing engine.
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        issue_date: date,
        maturity_date: date,
        face_value: float,
        spread: float,
        currency: Currency,
        counterparty_id: str,
        index_name: str = "SOFR",
        reset_frequency: PaymentFrequency = PaymentFrequency.QUARTERLY,
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        settlement_days: int = 2,
        credit_spread: float = 0.0,
        is_long: bool = True,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.FRN,
            asset_class=AssetClass.INTEREST_RATE,
            trade_date=trade_date,
            effective_date=issue_date,
            maturity_date=maturity_date,
            notional=face_value,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.face_value = face_value
        self.spread = spread
        self.index_name = index_name
        self.reset_frequency = reset_frequency
        self.day_count = day_count
        self.settlement_days = settlement_days
        self.credit_spread = credit_spread
        self.is_long = is_long
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the FRN using QuantLib."""
        if not QUANTLIB_AVAILABLE:
            raise RuntimeError("QuantLib not available")
        
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        ql.Settings.instance().evaluationDate = to_ql_date(valuation_date)
        
        calendar = get_ql_calendar(self.currency)
        
        # Build curves
        risky_curve = {
            t: r + self.credit_spread
            for t, r in market_data.discount_curve.items()
        }
        yield_curve = build_yield_curve(valuation_date, risky_curve, calendar)
        
        # Build schedule
        schedule = ql.Schedule(
            to_ql_date(self.effective_date),
            to_ql_date(self.maturity_date),
            ql.Period(get_ql_frequency(self.reset_frequency)),
            calendar,
            ql.ModifiedFollowing,
            ql.ModifiedFollowing,
            ql.DateGeneration.Backward,
            False
        )
        
        # Create index
        if self.index_name == "SOFR":
            index = ql.Sofr(yield_curve)
        elif self.index_name == "EURIBOR":
            index = ql.Euribor3M(yield_curve)
        else:
            index = ql.Sofr(yield_curve)
        
        # Build floating rate bond
        frn = ql.FloatingRateBond(
            self.settlement_days,
            self.face_value,
            schedule,
            index,
            get_ql_day_count(self.day_count),
            ql.ModifiedFollowing,
            2,  # fixingDays
            [1.0],  # gearings
            [self.spread]  # spreads
        )
        
        # Set pricing engine
        engine = ql.DiscountingBondEngine(yield_curve)
        frn.setPricingEngine(engine)
        
        # Get results
        npv = frn.NPV()
        dirty_price = frn.dirtyPrice()
        clean_price = frn.cleanPrice()
        accrued = frn.accruedAmount()
        
        if not self.is_long:
            npv = -npv
        
        # Duration is very short for FRN (to next reset)
        remaining_maturity = self.get_remaining_maturity(valuation_date)
        periods = 4 if self.reset_frequency == PaymentFrequency.QUARTERLY else 2
        duration = min(1.0 / periods, remaining_maturity)
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "dirty_price": dirty_price,
                "clean_price": clean_price,
                "accrued_interest": accrued,
                "price_pct": clean_price,
                "spread": self.spread,
                "credit_spread": self.credit_spread,
            },
            greeks={
                "dv01": self.face_value * duration * 0.0001,
                "duration": duration,
                "spread_dv01": self.face_value * remaining_maturity * 0.0001,
            },
            metadata={
                "product_type": self.product_type.value,
                "pricing_engine": "QuantLib.DiscountingBond",
                "index": self.index_name,
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure profile."""
        result = self.price(market_data)
        current_npv = max(0, result.npv)
        
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining_maturity)
        
        time_grid = list(np.linspace(0, horizon, 10))
        
        # FRN has low rate exposure, mainly credit
        ee_profile = [current_npv * max(0, 1 - t / remaining_maturity) for t in time_grid]
        pfe_profile = [e * 1.1 for e in ee_profile]
        
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
        """Calculate SA-CCR exposure."""
        result = self.price(market_data)
        rc = max(0, result.npv)
        
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        duration = result.greeks.get("duration", 0.25)
        
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining_maturity)
        
        effective_notional = self.face_value * duration
        delta = 1.0 if self.is_long else -1.0
        
        pfe_addon = sf * np.abs(delta) * effective_notional * mf
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.INTEREST_RATE
        )


# =============================================================================
# Zero Coupon Bond (QuantLib)
# =============================================================================

class ZeroCouponBondQL(BaseProduct):
    """
    Zero Coupon Bond using QuantLib pricing engine.
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        issue_date: date,
        maturity_date: date,
        face_value: float,
        currency: Currency,
        counterparty_id: str,
        settlement_days: int = 2,
        credit_spread: float = 0.0,
        is_long: bool = True,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.ZERO_COUPON_BOND,
            asset_class=AssetClass.INTEREST_RATE,
            trade_date=trade_date,
            effective_date=issue_date,
            maturity_date=maturity_date,
            notional=face_value,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.face_value = face_value
        self.settlement_days = settlement_days
        self.credit_spread = credit_spread
        self.is_long = is_long
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the zero coupon bond using QuantLib."""
        if not QUANTLIB_AVAILABLE:
            raise RuntimeError("QuantLib not available")
        
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        ql.Settings.instance().evaluationDate = to_ql_date(valuation_date)
        
        calendar = get_ql_calendar(self.currency)
        
        # Build curves
        risky_curve = {
            t: r + self.credit_spread
            for t, r in market_data.discount_curve.items()
        }
        yield_curve = build_yield_curve(valuation_date, risky_curve, calendar)
        
        # Build zero coupon bond
        zcb = ql.ZeroCouponBond(
            self.settlement_days,
            calendar,
            self.face_value,
            to_ql_date(self.maturity_date)
        )
        
        # Set pricing engine
        engine = ql.DiscountingBondEngine(yield_curve)
        zcb.setPricingEngine(engine)
        
        # Get results
        npv = zcb.NPV()
        clean_price = zcb.cleanPrice()
        
        remaining_maturity = self.get_remaining_maturity(valuation_date)
        
        # YTM
        ytm = bond_yield(zcb, clean_price, ql.Actual365Fixed(), ql.Compounded, ql.Annual)
        
        # Duration equals maturity for zero coupon
        duration = remaining_maturity
        
        if not self.is_long:
            npv = -npv
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "dirty_price": npv,
                "clean_price": clean_price,
                "price_pct": clean_price,
                "ytm": ytm,
                "macaulay_duration": duration,
                "modified_duration": duration / (1 + ytm),
            },
            greeks={
                "dv01": npv * duration * 0.0001 * (1 if self.is_long else -1),
                "duration": duration,
            },
            metadata={
                "product_type": self.product_type.value,
                "pricing_engine": "QuantLib.DiscountingBond",
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure profile."""
        result = self.price(market_data)
        current_npv = result.npv
        dv01 = result.greeks.get("dv01", 0)
        
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining_maturity)
        
        rate_vol = 0.01
        
        time_grid = list(np.linspace(0, horizon, 10))
        
        np.random.seed(42)
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            if t == 0:
                ee_profile.append(max(0, current_npv))
                pfe_profile.append(max(0, current_npv))
                continue
            
            rate_shocks = np.random.normal(0, rate_vol * np.sqrt(t), num_scenarios)
            npv_changes = dv01 * 10000 * rate_shocks
            
            time_factor = max(0, 1 - t / remaining_maturity) if remaining_maturity > 0 else 0
            simulated_npvs = (current_npv + npv_changes) * time_factor
            
            exposures = np.maximum(0, simulated_npvs)
            
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
        """Calculate SA-CCR exposure."""
        result = self.price(market_data)
        rc = max(0, result.npv)
        
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        duration = remaining_maturity
        
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining_maturity)
        
        effective_notional = self.face_value * duration
        delta = 1.0 if self.is_long else -1.0
        
        pfe_addon = sf * np.abs(delta) * effective_notional * mf
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.INTEREST_RATE
        )


__all__ = [
    "FixedRateBondQL",
    "FloatingRateBondQL",
    "ZeroCouponBondQL",
    "QUANTLIB_AVAILABLE",
]
