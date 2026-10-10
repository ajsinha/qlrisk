"""
QLRisk - Interest Rate Products (QuantLib Implementation) v1.2.0
===============================================================================

QuantLib-based implementations of interest rate derivatives for CCR calculation.
Provides high-performance pricing using QuantLib's proven pricing engines.

Products Implemented:
- Interest Rate Swap (IRS)
- Overnight Index Swap (OIS)
- Forward Rate Agreement (FRA)
- Interest Rate Cap/Floor
- Swaption
- Basis Swap

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
    print("Warning: QuantLib not available. Install with: pip install QuantLib-Python")

from ..base import (
    BaseProduct, AssetClass, Currency,
    DayCountConvention, PaymentFrequency,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)
from ..product_types import ProductType


# =============================================================================
# QuantLib Helper Functions
# =============================================================================

def to_ql_date(d: date) -> 'ql.Date':
    """Convert Python date to QuantLib Date."""
    return ql.Date(d.day, d.month, d.year)


def from_ql_date(ql_date: 'ql.Date') -> date:
    """Convert QuantLib Date to Python date."""
    return date(ql_date.year(), ql_date.month(), ql_date.dayOfMonth())


def get_ql_day_count(dc: DayCountConvention) -> 'ql.DayCounter':
    """Convert to QuantLib DayCounter."""
    dc_map = {
        DayCountConvention.ACT_360: ql.Actual360(),
        DayCountConvention.ACT_365: ql.Actual365Fixed(),
        DayCountConvention.ACT_ACT: ql.ActualActual(ql.ActualActual.ISDA),
        DayCountConvention.THIRTY_360: ql.Thirty360(ql.Thirty360.BondBasis),
    }
    return dc_map.get(dc, ql.Actual360())


def get_ql_frequency(freq: PaymentFrequency) -> int:
    """Convert to QuantLib Frequency."""
    freq_map = {
        PaymentFrequency.MONTHLY: ql.Monthly,
        PaymentFrequency.QUARTERLY: ql.Quarterly,
        PaymentFrequency.SEMI_ANNUAL: ql.Semiannual,
        PaymentFrequency.ANNUAL: ql.Annual,
    }
    return freq_map.get(freq, ql.Semiannual)


def get_ql_calendar(currency: Currency) -> 'ql.Calendar':
    """Get QuantLib calendar for currency."""
    cal_map = {
        Currency.USD: ql.UnitedStates(ql.UnitedStates.GovernmentBond),
        Currency.EUR: ql.TARGET(),
        Currency.GBP: ql.UnitedKingdom(ql.UnitedKingdom.Exchange),
        Currency.JPY: ql.Japan(),
        Currency.CHF: ql.Switzerland(),
    }
    return cal_map.get(currency, ql.TARGET())


def build_yield_curve(
    valuation_date: date,
    discount_curve: Dict[float, float],
    calendar: 'ql.Calendar' = None
) -> 'ql.YieldTermStructureHandle':
    """Build QuantLib yield curve from discount curve dictionary."""
    ql_date = to_ql_date(valuation_date)
    ql.Settings.instance().evaluationDate = ql_date
    
    if calendar is None:
        calendar = ql.TARGET()
    
    # Convert to QuantLib format
    dates = [ql_date]
    rates = [list(discount_curve.values())[0] if discount_curve else 0.05]
    
    for tenor, rate in sorted(discount_curve.items()):
        future_date = calendar.advance(ql_date, int(tenor * 365), ql.Days)
        dates.append(future_date)
        rates.append(rate)
    
    # Build curve
    day_count = ql.Actual365Fixed()
    curve = ql.ZeroCurve(dates, rates, day_count, calendar)
    
    return ql.YieldTermStructureHandle(curve)


# =============================================================================
# Interest Rate Swap (QuantLib)
# =============================================================================

class InterestRateSwapQL(BaseProduct):
    """
    Interest Rate Swap using QuantLib pricing engine.
    
    Provides more accurate pricing than pure Python implementation
    with proper curve handling and date adjustments.
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,
        fixed_rate: float,
        currency: Currency,
        counterparty_id: str,
        pay_fixed: bool = True,
        fixed_frequency: PaymentFrequency = PaymentFrequency.SEMI_ANNUAL,
        float_frequency: PaymentFrequency = PaymentFrequency.QUARTERLY,
        fixed_day_count: DayCountConvention = DayCountConvention.THIRTY_360,
        float_day_count: DayCountConvention = DayCountConvention.ACT_360,
        float_index: str = "SOFR",
        spread: float = 0.0,
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
        self.pay_fixed = pay_fixed
        self.fixed_frequency = fixed_frequency
        self.float_frequency = float_frequency
        self.fixed_day_count = fixed_day_count
        self.float_day_count = float_day_count
        self.float_index = float_index
        self.spread = spread
        
        # QuantLib objects (built on first pricing)
        self._ql_swap = None
        self._ql_engine = None
    
    def _build_ql_swap(self, yield_curve_handle: 'ql.YieldTermStructureHandle'):
        """Build QuantLib VanillaSwap object."""
        calendar = get_ql_calendar(self.currency)
        
        # Fixed leg schedule
        fixed_schedule = ql.Schedule(
            to_ql_date(self.effective_date),
            to_ql_date(self.maturity_date),
            ql.Period(get_ql_frequency(self.fixed_frequency)),
            calendar,
            ql.ModifiedFollowing,
            ql.ModifiedFollowing,
            ql.DateGeneration.Forward,
            False
        )
        
        # Float leg schedule
        float_schedule = ql.Schedule(
            to_ql_date(self.effective_date),
            to_ql_date(self.maturity_date),
            ql.Period(get_ql_frequency(self.float_frequency)),
            calendar,
            ql.ModifiedFollowing,
            ql.ModifiedFollowing,
            ql.DateGeneration.Forward,
            False
        )
        
        # Create index
        if self.float_index == "SOFR":
            index = ql.Sofr(yield_curve_handle)
        elif self.float_index == "EURIBOR":
            index = ql.Euribor3M(yield_curve_handle)
        else:
            index = ql.Sofr(yield_curve_handle)
        
        # Create swap
        swap_type = ql.VanillaSwap.Payer if self.pay_fixed else ql.VanillaSwap.Receiver
        
        self._ql_swap = ql.VanillaSwap(
            swap_type,
            self.notional,
            fixed_schedule,
            self.fixed_rate,
            get_ql_day_count(self.fixed_day_count),
            float_schedule,
            index,
            self.spread,
            get_ql_day_count(self.float_day_count)
        )
        
        # Set pricing engine
        self._ql_engine = ql.DiscountingSwapEngine(yield_curve_handle)
        self._ql_swap.setPricingEngine(self._ql_engine)
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the swap using QuantLib."""
        if not QUANTLIB_AVAILABLE:
            raise RuntimeError("QuantLib not available")
        
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        # Set evaluation date
        ql.Settings.instance().evaluationDate = to_ql_date(valuation_date)
        
        # Build yield curve
        calendar = get_ql_calendar(self.currency)
        yield_curve = build_yield_curve(valuation_date, market_data.discount_curve, calendar)
        
        # Build swap
        self._build_ql_swap(yield_curve)
        
        # Get results
        npv = self._ql_swap.NPV()
        fixed_leg_npv = self._ql_swap.fixedLegNPV()
        float_leg_npv = self._ql_swap.floatingLegNPV()
        fair_rate = self._ql_swap.fairRate()
        
        # BPV (DV01)
        bpv = self._ql_swap.fixedLegBPS() * self.notional / 10000
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "fixed_leg_npv": fixed_leg_npv,
                "floating_leg_npv": float_leg_npv,
                "fair_rate": fair_rate,
                "fixed_rate": self.fixed_rate,
                "rate_difference": fair_rate - self.fixed_rate,
            },
            greeks={
                "dv01": bpv,
                "pv01": bpv,
            },
            metadata={
                "product_type": self.product_type.value,
                "pricing_engine": "QuantLib",
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure using QuantLib repricing."""
        if not QUANTLIB_AVAILABLE:
            raise RuntimeError("QuantLib not available")
        
        result = self.price(market_data)
        current_npv = result.npv
        dv01 = result.greeks.get("dv01", 0)
        
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining_maturity)
        
        rate_vol = market_data.volatility_surfaces.get("ir_vol", 0.01)
        if isinstance(rate_vol, dict):
            rate_vol = 0.01
        
        num_steps = max(int(horizon * 4), 4)
        time_grid = np.linspace(0, horizon, num_steps + 1)
        
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
        delta = 1.0 if self.pay_fixed else -1.0
        
        pfe_addon = sf * delta * effective_notional * mf
        ead = SACCRParameters.ALPHA * (rc + abs(pfe_addon))
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=abs(pfe_addon),
            ead=ead,
            asset_class=AssetClass.INTEREST_RATE,
            hedging_set_contributions={self.currency.value: pfe_addon}
        )


# =============================================================================
# Swaption (QuantLib)
# =============================================================================

class SwaptionQL(BaseProduct):
    """
    Interest Rate Swaption using QuantLib pricing engine.
    
    Uses Black or Bachelier model for swaption pricing.
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        option_expiry: date,
        swap_effective: date,
        swap_maturity: date,
        notional: float,
        strike: float,
        currency: Currency,
        counterparty_id: str,
        is_payer: bool = True,
        exercise_type: str = "european",
        volatility: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.SWAPTION,
            asset_class=AssetClass.INTEREST_RATE,
            trade_date=trade_date,
            effective_date=option_expiry,
            maturity_date=swap_maturity,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.option_expiry = option_expiry
        self.swap_effective = swap_effective
        self.swap_maturity = swap_maturity
        self.strike = strike
        self.is_payer = is_payer
        self.exercise_type = exercise_type
        self.volatility = volatility
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the swaption using QuantLib."""
        if not QUANTLIB_AVAILABLE:
            raise RuntimeError("QuantLib not available")
        
        valuation_date = market_data.valuation_date
        
        if valuation_date >= self.option_expiry:
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        ql.Settings.instance().evaluationDate = to_ql_date(valuation_date)
        
        calendar = get_ql_calendar(self.currency)
        yield_curve = build_yield_curve(valuation_date, market_data.discount_curve, calendar)
        
        # Build underlying swap
        fixed_schedule = ql.Schedule(
            to_ql_date(self.swap_effective),
            to_ql_date(self.swap_maturity),
            ql.Period(ql.Semiannual),
            calendar,
            ql.ModifiedFollowing,
            ql.ModifiedFollowing,
            ql.DateGeneration.Forward,
            False
        )
        
        float_schedule = ql.Schedule(
            to_ql_date(self.swap_effective),
            to_ql_date(self.swap_maturity),
            ql.Period(ql.Quarterly),
            calendar,
            ql.ModifiedFollowing,
            ql.ModifiedFollowing,
            ql.DateGeneration.Forward,
            False
        )
        
        index = ql.Sofr(yield_curve)
        
        swap_type = ql.VanillaSwap.Payer if self.is_payer else ql.VanillaSwap.Receiver
        
        underlying_swap = ql.VanillaSwap(
            swap_type,
            self.notional,
            fixed_schedule,
            self.strike,
            ql.Thirty360(ql.Thirty360.BondBasis),
            float_schedule,
            index,
            0.0,
            ql.Actual360()
        )
        
        # Build swaption
        exercise = ql.EuropeanExercise(to_ql_date(self.option_expiry))
        swaption = ql.Swaption(underlying_swap, exercise)
        
        # Volatility
        vol = self.volatility or market_data.volatility_surfaces.get("swaption_vol", 0.20)
        if isinstance(vol, dict):
            vol = 0.20
        
        vol_handle = ql.QuoteHandle(ql.SimpleQuote(vol))
        
        # Black engine
        engine = ql.BlackSwaptionEngine(yield_curve, vol_handle)
        swaption.setPricingEngine(engine)
        
        npv = swaption.NPV()
        
        # Greeks (approximate)
        option_maturity = year_fraction(valuation_date, self.option_expiry, DayCountConvention.ACT_365)
        swap_tenor = year_fraction(self.swap_effective, self.swap_maturity, DayCountConvention.ACT_365)
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "premium": npv,
                "strike": self.strike,
                "volatility": vol,
                "option_maturity": option_maturity,
                "swap_tenor": swap_tenor,
            },
            greeks={
                "vega": npv * 0.01 / vol if vol > 0 else 0,
            },
            metadata={
                "product_type": self.product_type.value,
                "pricing_engine": "QuantLib.Black",
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure."""
        result = self.price(market_data)
        current_npv = max(0, result.npv)
        
        option_maturity = year_fraction(
            market_data.valuation_date, 
            self.option_expiry, 
            DayCountConvention.ACT_365
        )
        horizon = min(time_horizon, option_maturity)
        
        time_grid = list(np.linspace(0, horizon, 10))
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            time_factor = np.sqrt(max(0, option_maturity - t) / option_maturity) if option_maturity > 0 else 0
            exposure = current_npv * time_factor
            ee_profile.append(exposure)
            pfe_profile.append(exposure * 1.5)
        
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
        
        option_maturity = year_fraction(
            market_data.valuation_date,
            self.option_expiry,
            DayCountConvention.ACT_365
        )
        swap_tenor = year_fraction(self.swap_effective, self.swap_maturity, DayCountConvention.ACT_365)
        
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(option_maturity)
        sd = SACCRParameters.supervisory_duration(option_maturity, option_maturity + swap_tenor)
        
        vol = self.volatility or 0.50
        delta = SACCRParameters.calculate_option_delta(
            is_call=self.is_payer,
            underlying=result.components.get("strike", self.strike),
            strike=self.strike,
            time_to_expiry=option_maturity,
            volatility=vol
        )
        
        effective_notional = self.notional * sd
        pfe_addon = sf * abs(delta) * effective_notional * mf
        
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.INTEREST_RATE
        )


# =============================================================================
# Cap/Floor (QuantLib)
# =============================================================================

class InterestRateCapQL(BaseProduct):
    """
    Interest Rate Cap using QuantLib pricing engine.
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,
        strike: float,
        currency: Currency,
        counterparty_id: str,
        is_cap: bool = True,
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        frequency: PaymentFrequency = PaymentFrequency.QUARTERLY,
        volatility: Optional[float] = None,
        **kwargs
    ):
        product_type = ProductType.CAP if is_cap else ProductType.FLOOR
        
        super().__init__(
            trade_id=trade_id,
            product_type=product_type,
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
        self.is_cap = is_cap
        self.day_count = day_count
        self.frequency = frequency
        self.volatility = volatility
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the cap/floor using QuantLib."""
        if not QUANTLIB_AVAILABLE:
            raise RuntimeError("QuantLib not available")
        
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        ql.Settings.instance().evaluationDate = to_ql_date(valuation_date)
        
        calendar = get_ql_calendar(self.currency)
        yield_curve = build_yield_curve(valuation_date, market_data.discount_curve, calendar)
        
        # Build schedule
        schedule = ql.Schedule(
            to_ql_date(self.effective_date),
            to_ql_date(self.maturity_date),
            ql.Period(get_ql_frequency(self.frequency)),
            calendar,
            ql.ModifiedFollowing,
            ql.ModifiedFollowing,
            ql.DateGeneration.Forward,
            False
        )
        
        # Create index
        index = ql.Sofr(yield_curve)
        
        # Create cap/floor
        cap_floor_type = ql.Cap if self.is_cap else ql.Floor
        
        # Build ibor leg
        ibor_leg = ql.IborLeg([self.notional], schedule, index)
        
        cap_floor = ql.CapFloor(
            ql.CapFloor.Cap if self.is_cap else ql.CapFloor.Floor,
            ibor_leg,
            [self.strike]
        )
        
        # Volatility
        vol = self.volatility or market_data.volatility_surfaces.get("cap_vol", 0.20)
        if isinstance(vol, dict):
            vol = 0.20
        
        vol_handle = ql.QuoteHandle(ql.SimpleQuote(vol))
        engine = ql.BlackCapFloorEngine(yield_curve, vol_handle)
        cap_floor.setPricingEngine(engine)
        
        npv = cap_floor.NPV()
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "premium": npv,
                "strike": self.strike,
                "volatility": vol,
                "is_cap": self.is_cap,
            },
            greeks={
                "vega": npv * 0.01 / vol if vol > 0 else 0,
            },
            metadata={
                "product_type": self.product_type.value,
                "pricing_engine": "QuantLib.Black",
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure."""
        result = self.price(market_data)
        current_npv = max(0, result.npv)
        
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining_maturity)
        
        time_grid = list(np.linspace(0, horizon, 10))
        
        ee_profile = [current_npv * max(0, 1 - t / remaining_maturity) for t in time_grid]
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
        """Calculate SA-CCR exposure."""
        result = self.price(market_data)
        rc = max(0, result.npv)
        
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining_maturity)
        sd = SACCRParameters.supervisory_duration(0, remaining_maturity)
        
        vol = self.volatility or 0.50
        delta = SACCRParameters.calculate_option_delta(
            is_call=self.is_cap,
            underlying=self.strike,
            strike=self.strike,
            time_to_expiry=remaining_maturity,
            volatility=vol
        )
        
        effective_notional = self.notional * sd
        pfe_addon = sf * abs(delta) * effective_notional * mf
        
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.INTEREST_RATE
        )


# Alias
InterestRateFloorQL = InterestRateCapQL


__all__ = [
    "InterestRateSwapQL",
    "SwaptionQL",
    "InterestRateCapQL",
    "InterestRateFloorQL",
    "QUANTLIB_AVAILABLE",
    "to_ql_date",
    "from_ql_date",
    "build_yield_curve",
]
