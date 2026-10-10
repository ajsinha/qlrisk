"""
QLRisk - Interest Rate Products (Python Implementation)
======================================================================

Pure Python implementations of interest rate derivative products including:
- Interest Rate Swaps (IRS)
- Overnight Index Swaps (OIS)
- Forward Rate Agreements (FRA)
- Basis Swaps
- Interest Rate Caps, Floors, and Collars
- Swaptions
- Inflation Swaps
- Zero Coupon Swaps
- Amortizing Swaps

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq

from ..base import curve_value
from ..base import (
    BaseProduct, ProductType, AssetClass, Currency, FloatingRateIndex,
    DayCountConvention, PaymentFrequency, BusinessDayConvention,
    OptionType, OptionStyle, SettlementType,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction, discount_factor, forward_rate,
    bachelier_call, bachelier_put
)


# =============================================================================
# Interest Rate Swap (IRS)
# =============================================================================

@dataclass
class IRSLeg:
    """Specification of a single swap leg."""
    is_fixed: bool
    rate: Optional[float] = None  # Fixed rate or spread
    index: Optional[FloatingRateIndex] = None
    frequency: PaymentFrequency = PaymentFrequency.QUARTERLY
    day_count: DayCountConvention = DayCountConvention.ACT_360
    notional: float = 0.0
    currency: Currency = Currency.USD


class InterestRateSwap(BaseProduct):
    """
    Interest Rate Swap product.
    
    Exchange of fixed-rate for floating-rate interest payments.
    Supports standard vanilla swaps, forward-starting, and amortizing.
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
        floating_index: FloatingRateIndex,
        is_payer: bool = True,  # True = pay fixed, receive float
        fixed_frequency: PaymentFrequency = PaymentFrequency.SEMI_ANNUAL,
        float_frequency: PaymentFrequency = PaymentFrequency.QUARTERLY,
        fixed_day_count: DayCountConvention = DayCountConvention.THIRTY_360,
        float_day_count: DayCountConvention = DayCountConvention.ACT_360,
        spread: float = 0.0,  # Spread on floating leg
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
    
    def generate_schedule(
        self,
        frequency: PaymentFrequency
    ) -> List[Tuple[date, date]]:
        """Generate payment schedule (start_date, end_date) tuples."""
        schedule = []
        current_date = self.effective_date
        
        # Frequency to months mapping
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
        """Get notional amount considering amortization."""
        if not self.amortization_schedule:
            return self.notional
        
        current_notional = self.notional
        for amort_date, amort_amount in sorted(self.amortization_schedule):
            if as_of_date >= amort_date:
                current_notional -= amort_amount
        
        return max(0, current_notional)
    
    def price(self, market_data: MarketData) -> PricingResult:
        """
        Price the interest rate swap.
        
        Args:
            market_data: Market data including discount curve and forward curve
            
        Returns:
            PricingResult with NPV and Greeks
        """
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        # Get curves
        discount_curve = market_data.discount_curve
        forward_curve = market_data.forward_curves.get(
            self.floating_index.value, discount_curve
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
            
            # Get discount factor
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
            
            # Get forward rate and discount factor
            df_start = np.exp(-curve_value(forward_curve, t_start, 0.05) * t_start) if t_start > 0 else 1.0
            df_end = np.exp(-curve_value(forward_curve, t_end, 0.05) * t_end)
            
            if t_end > t_start and t_start >= 0:
                fwd_rate = (df_start / df_end - 1) / tau
            else:
                fwd_rate = curve_value(forward_curve, t_end, 0.05)
            
            df_discount = np.exp(-curve_value(discount_curve, t_end, 0.05) * t_end)
            float_pv += notional * (fwd_rate + self.spread) * tau * df_discount
        
        # Calculate NPV based on position
        if self.is_payer:
            npv = float_pv - fixed_pv
        else:
            npv = fixed_pv - float_pv
        
        # Calculate par rate
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
                "duration": fixed_dv01 / max(abs(npv), 1) * 10000 if npv != 0 else 0,
            },
            metadata={
                "product_type": self.product_type.value,
                "is_payer": self.is_payer,
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure profile using Monte Carlo simulation."""
        
        valuation_date = market_data.valuation_date
        remaining_maturity = self.get_remaining_maturity(valuation_date)
        horizon = min(time_horizon, remaining_maturity)
        
        if horizon <= 0:
            return CCRExposureProfile(
                time_grid=[0.0],
                expected_exposure=[0.0],
                potential_future_exposure=[0.0],
                effective_ee=[0.0],
                peak_exposure=0.0,
                epe=0.0,
                effective_epe=0.0,
                cva=0.0
            )
        
        # Time grid
        num_steps = max(int(horizon * 4), 4)  # Quarterly
        time_grid = np.linspace(0, horizon, num_steps + 1)
        
        # Get current pricing
        current_result = self.price(market_data)
        current_npv = current_result.npv
        current_dv01 = current_result.greeks.get("dv01", self.notional * 0.0001)
        
        # Rate volatility (annualized)
        vol = market_data.volatility_surfaces.get("ir_vol", 0.01)  # 1% normal vol
        
        # Monte Carlo simulation
        np.random.seed(42)
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            if t == 0:
                ee_profile.append(max(0, current_npv))
                pfe_profile.append(max(0, current_npv))
                continue
            
            # Simulate rate changes (normal distribution for rates)
            rate_changes = np.random.normal(0, vol * np.sqrt(t), num_scenarios)
            
            # Approximate NPV changes
            npv_changes = current_dv01 * 10000 * rate_changes
            simulated_npvs = current_npv + npv_changes
            
            # Adjust for time decay (reduced sensitivity as maturity approaches)
            time_factor = max(0, 1 - t / remaining_maturity)
            simulated_npvs *= time_factor
            
            # Exposure = max(0, NPV)
            exposures = np.maximum(0, simulated_npvs)
            
            ee_profile.append(np.mean(exposures))
            pfe_profile.append(np.percentile(exposures, confidence_level * 100))
        
        # Calculate Effective EE (non-decreasing)
        effective_ee = [ee_profile[0]]
        for ee in ee_profile[1:]:
            effective_ee.append(max(ee, effective_ee[-1]))
        
        # Calculate EPE and Effective EPE
        epe = np.mean(ee_profile)
        effective_epe = np.mean(effective_ee)
        
        # Simple CVA calculation
        lgd = 0.6  # Assumed LGD
        credit_spread = market_data.credit_curves.get(
            self.counterparty_id, {}
        ).get(1.0, 0.01)
        
        cva = lgd * sum(
            ee * (1 - np.exp(-credit_spread * t))
            for ee, t in zip(ee_profile, time_grid)
        ) / len(time_grid)
        
        return CCRExposureProfile(
            time_grid=list(time_grid),
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=effective_ee,
            peak_exposure=max(pfe_profile),
            epe=epe,
            effective_epe=effective_epe,
            cva=cva,
            metadata={
                "num_scenarios": num_scenarios,
                "confidence_level": confidence_level,
                "method": "monte_carlo",
            }
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """Calculate SA-CCR exposure."""
        valuation_date = market_data.valuation_date
        
        # Replacement Cost
        result = self.price(market_data)
        rc = max(0, result.npv)
        
        # PFE Add-on
        remaining_maturity = self.get_remaining_maturity(valuation_date)
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining_maturity)
        
        # Effective notional
        duration = min(remaining_maturity, 5.0)  # Cap at 5 years for duration
        effective_notional = self.notional * duration
        
        # Delta (±1 for linear products)
        delta = 1.0 if self.is_payer else -1.0
        
        pfe_addon = sf * np.abs(delta) * effective_notional * mf
        
        # EAD
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.INTEREST_RATE,
            hedging_set_contributions={self.currency.value: pfe_addon},
            metadata={
                "supervisory_factor": sf,
                "maturity_factor": mf,
                "effective_notional": effective_notional,
                "duration": duration,
            }
        )


# =============================================================================
# Overnight Index Swap (OIS)
# =============================================================================

class OvernightIndexSwap(InterestRateSwap):
    """
    Overnight Index Swap (OIS).
    
    Exchange of fixed rate for compounded overnight rate (SOFR, ESTR, etc.).
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
        overnight_index: FloatingRateIndex,
        is_payer: bool = True,
        payment_frequency: PaymentFrequency = PaymentFrequency.ANNUAL,
        **kwargs
    ):
        # Map overnight indices
        if overnight_index not in [
            FloatingRateIndex.SOFR, FloatingRateIndex.ESTR,
            FloatingRateIndex.SONIA, FloatingRateIndex.TONA,
            FloatingRateIndex.SARON
        ]:
            overnight_index = FloatingRateIndex.SOFR
        
        super().__init__(
            trade_id=trade_id,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            fixed_rate=fixed_rate,
            floating_index=overnight_index,
            is_payer=is_payer,
            fixed_frequency=payment_frequency,
            float_frequency=payment_frequency,
            fixed_day_count=DayCountConvention.ACT_360,
            float_day_count=DayCountConvention.ACT_360,
            **kwargs
        )
        
        self.product_type = ProductType.OIS
        self.overnight_index = overnight_index


# =============================================================================
# Forward Rate Agreement (FRA)
# =============================================================================

class ForwardRateAgreement(BaseProduct):
    """
    Forward Rate Agreement (FRA).
    
    Agreement to exchange interest payments at a future date based on
    a notional principal and agreed forward rate.
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,  # Settlement date
        maturity_date: date,   # End of FRA period
        notional: float,
        currency: Currency,
        counterparty_id: str,
        fra_rate: float,       # Agreed forward rate
        floating_index: FloatingRateIndex,
        is_payer: bool = True,  # True = pay fixed (FRA rate)
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.FRA,
            asset_class=AssetClass.INTEREST_RATE,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.fra_rate = fra_rate
        self.floating_index = floating_index
        self.is_payer = is_payer
        self.day_count = day_count
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the FRA."""
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        discount_curve = market_data.discount_curve
        forward_curve = market_data.forward_curves.get(
            self.floating_index.value, discount_curve
        )
        
        # Time to settlement and maturity
        t_settle = year_fraction(valuation_date, self.effective_date, DayCountConvention.ACT_365)
        t_end = year_fraction(valuation_date, self.maturity_date, DayCountConvention.ACT_365)
        
        # FRA period
        tau = year_fraction(self.effective_date, self.maturity_date, self.day_count)
        
        # Forward rate
        df_settle = np.exp(-curve_value(forward_curve, t_settle, 0.05) * t_settle) if t_settle > 0 else 1.0
        df_end = np.exp(-curve_value(forward_curve, t_end, 0.05) * t_end)
        
        if t_end > t_settle:
            fwd_rate = (df_settle / df_end - 1) / tau
        else:
            fwd_rate = curve_value(forward_curve, t_end, 0.05)
        
        # Discount factor to settlement
        df_discount = np.exp(-curve_value(discount_curve, t_settle, 0.05) * t_settle)
        
        # NPV (cash settlement at effective date)
        rate_diff = fwd_rate - self.fra_rate
        cash_flow = self.notional * rate_diff * tau / (1 + fwd_rate * tau)
        
        if not self.is_payer:
            cash_flow = -cash_flow
        
        npv = cash_flow * df_discount
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "forward_rate": fwd_rate,
                "fra_rate": self.fra_rate,
                "rate_difference": rate_diff,
                "cash_flow": cash_flow,
            },
            greeks={
                "dv01": self.notional * tau * df_discount * 0.0001,
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
        t_settle = year_fraction(valuation_date, self.effective_date, DayCountConvention.ACT_365)
        
        # FRA exposure is concentrated at settlement
        time_grid = [0.0, t_settle] if t_settle > 0 else [0.0]
        
        result = self.price(market_data)
        current_exposure = max(0, result.npv)
        
        # Simple simulation for peak exposure
        vol = market_data.volatility_surfaces.get("ir_vol", 0.01)
        dv01 = result.greeks.get("dv01", self.notional * 0.0001)
        
        z_score = norm.ppf(confidence_level)
        max_rate_move = z_score * vol * np.sqrt(t_settle) if t_settle > 0 else 0
        peak_exposure = current_exposure + abs(dv01) * 10000 * max_rate_move
        
        ee_profile = [current_exposure, peak_exposure] if len(time_grid) > 1 else [current_exposure]
        pfe_profile = [current_exposure, peak_exposure] if len(time_grid) > 1 else [current_exposure]
        
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=ee_profile,
            peak_exposure=peak_exposure,
            epe=np.mean(ee_profile),
            effective_epe=np.mean(ee_profile),
            cva=0.0,
            metadata={"method": "analytical"}
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """Calculate SA-CCR exposure."""
        result = self.price(market_data)
        rc = max(0, result.npv)
        
        valuation_date = market_data.valuation_date
        remaining_maturity = self.get_remaining_maturity(valuation_date)
        
        # FRA has start and end dates - use supervisory duration
        t_start = year_fraction(valuation_date, self.effective_date, DayCountConvention.ACT_365)
        t_end = year_fraction(valuation_date, self.maturity_date, DayCountConvention.ACT_365)
        
        # Supervisory duration
        sd = (np.exp(-0.05 * max(0, t_start)) - np.exp(-0.05 * t_end)) / 0.05
        
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining_maturity)
        
        effective_notional = self.notional * sd
        delta = 1.0 if self.is_payer else -1.0
        
        pfe_addon = sf * np.abs(delta) * effective_notional * mf
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.INTEREST_RATE,
            metadata={"supervisory_duration": sd}
        )


# =============================================================================
# Interest Rate Cap/Floor
# =============================================================================

class InterestRateCap(BaseProduct):
    """
    Interest Rate Cap.
    
    Series of call options (caplets) on a floating rate index.
    Pays max(0, Index - Strike) at each reset date.
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
        strike: float,
        floating_index: FloatingRateIndex,
        is_cap: bool = True,  # True = Cap, False = Floor
        frequency: PaymentFrequency = PaymentFrequency.QUARTERLY,
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.CAP if is_cap else ProductType.FLOOR,
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
        self.floating_index = floating_index
        self.is_cap = is_cap
        self.frequency = frequency
        self.day_count = day_count
    
    def generate_schedule(self) -> List[Tuple[date, date]]:
        """Generate caplet/floorlet schedule."""
        schedule = []
        current_date = self.effective_date
        
        freq_months = {
            PaymentFrequency.MONTHLY: 1,
            PaymentFrequency.QUARTERLY: 3,
            PaymentFrequency.SEMI_ANNUAL: 6,
        }
        
        months = freq_months.get(self.frequency, 3)
        
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
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the cap/floor using Black model."""
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        discount_curve = market_data.discount_curve
        forward_curve = market_data.forward_curves.get(
            self.floating_index.value, discount_curve
        )
        
        # Get cap/floor volatility
        vol_surface = market_data.volatility_surfaces.get("cap_vol", {})
        
        schedule = self.generate_schedule()
        total_npv = 0.0
        caplet_values = []
        
        for start, end in schedule:
            if end <= valuation_date:
                continue
            
            tau = year_fraction(start, end, self.day_count)
            t_fix = year_fraction(valuation_date, start, DayCountConvention.ACT_365)
            t_pay = year_fraction(valuation_date, end, DayCountConvention.ACT_365)
            
            if t_fix <= 0:
                continue
            
            # Forward rate
            df_start = np.exp(-curve_value(forward_curve, t_fix, 0.05) * t_fix)
            df_end = np.exp(-curve_value(forward_curve, t_pay, 0.05) * t_pay)
            fwd_rate = (df_start / df_end - 1) / tau
            
            # Discount factor
            df_discount = np.exp(-curve_value(discount_curve, t_pay, 0.05) * t_pay)
            
            # Volatility (use flat vol if surface not available)
            vol = vol_surface.get(t_fix, 0.15)  # 15% normal vol default
            
            # Bachelier (normal) model pricing
            if self.is_cap:
                caplet = bachelier_call(fwd_rate, self.strike, t_fix, vol, 1.0)
            else:
                caplet = bachelier_put(fwd_rate, self.strike, t_fix, vol, 1.0)
            
            caplet_value = self.notional * tau * caplet * df_discount
            total_npv += caplet_value
            caplet_values.append({
                "fixing_date": start.isoformat(),
                "forward_rate": fwd_rate,
                "caplet_value": caplet_value,
            })
        
        return PricingResult(
            npv=total_npv,
            currency=self.currency.value,
            components={
                "num_caplets": len(caplet_values),
                "caplet_details": caplet_values,
            },
            greeks={
                "vega": total_npv * 0.01,  # Approximate
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
        result = self.price(market_data)
        current_npv = result.npv
        
        # Options have positive exposure equal to their value
        # (buyer has positive exposure, seller has zero or margin)
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining_maturity)
        
        num_steps = max(int(horizon * 4), 4)
        time_grid = list(np.linspace(0, horizon, num_steps + 1))
        
        # For bought options, EE decays over time
        ee_profile = [
            max(0, current_npv * (1 - t / remaining_maturity))
            for t in time_grid
        ]
        pfe_profile = ee_profile.copy()  # For options, PFE ≈ EE
        
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=ee_profile,
            peak_exposure=max(pfe_profile),
            epe=np.mean(ee_profile),
            effective_epe=np.mean(ee_profile),
            cva=0.0,
            metadata={"method": "option_decay"}
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """Calculate SA-CCR exposure."""
        result = self.price(market_data)
        rc = result.npv  # For options, RC = max(0, V - C)
        
        valuation_date = market_data.valuation_date
        remaining_maturity = self.get_remaining_maturity(valuation_date)
        
        # Option delta approximation
        forward_curve = market_data.forward_curves.get(
            self.floating_index.value, market_data.discount_curve
        )
        avg_fwd = curve_value(forward_curve, remaining_maturity / 2, 0.05)
        
        # Black delta
        vol = market_data.volatility_surfaces.get("cap_vol", {}).get(remaining_maturity, 0.15)
        d1 = (avg_fwd - self.strike) / (vol * np.sqrt(remaining_maturity)) if vol > 0 else 0
        
        if self.is_cap:
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1
        
        # Supervisory duration
        sd = (1 - np.exp(-0.05 * remaining_maturity)) / 0.05
        
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(remaining_maturity)
        
        effective_notional = self.notional * sd
        pfe_addon = sf * np.abs(delta) * effective_notional * mf
        
        ead = SACCRParameters.ALPHA * (max(0, rc) + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=max(0, rc),
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.INTEREST_RATE,
            metadata={"delta": delta, "supervisory_duration": sd}
        )


class InterestRateFloor(InterestRateCap):
    """Interest Rate Floor - series of put options on floating rate."""
    
    def __init__(self, *args, **kwargs):
        kwargs['is_cap'] = False
        super().__init__(*args, **kwargs)


# =============================================================================
# Swaption
# =============================================================================

class Swaption(BaseProduct):
    """
    Swaption - Option on an Interest Rate Swap.
    
    Right (but not obligation) to enter into an IRS at a future date
    at a predetermined fixed rate.
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        expiry_date: date,
        effective_date: date,  # Underlying swap start
        maturity_date: date,   # Underlying swap maturity
        notional: float,
        currency: Currency,
        counterparty_id: str,
        strike: float,         # Fixed rate of underlying swap
        floating_index: FloatingRateIndex,
        option_type: OptionType = OptionType.CALL,  # Call = payer swaption
        style: OptionStyle = OptionStyle.EUROPEAN,
        settlement: SettlementType = SettlementType.PHYSICAL,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.SWAPTION,
            asset_class=AssetClass.INTEREST_RATE,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.expiry_date = expiry_date
        self.strike = strike
        self.floating_index = floating_index
        self.option_type = option_type
        self.style = style
        self.settlement = settlement
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price swaption using Black (normal) model."""
        valuation_date = market_data.valuation_date
        
        if valuation_date >= self.expiry_date:
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        discount_curve = market_data.discount_curve
        forward_curve = market_data.forward_curves.get(
            self.floating_index.value, discount_curve
        )
        
        # Time to expiry
        t_expiry = year_fraction(valuation_date, self.expiry_date, DayCountConvention.ACT_365)
        
        # Calculate forward swap rate
        swap_tenor = year_fraction(self.effective_date, self.maturity_date, DayCountConvention.ACT_365)
        
        # Simplified: use average forward rate
        t_start = year_fraction(valuation_date, self.effective_date, DayCountConvention.ACT_365)
        t_end = year_fraction(valuation_date, self.maturity_date, DayCountConvention.ACT_365)
        
        df_start = np.exp(-curve_value(forward_curve, t_start, 0.05) * t_start) if t_start > 0 else 1.0
        df_end = np.exp(-curve_value(forward_curve, t_end, 0.05) * t_end)
        
        # Annuity factor (simplified)
        num_periods = int(swap_tenor * 2)  # Semi-annual
        annuity = sum(
            0.5 * np.exp(-curve_value(discount_curve, t_start + i * 0.5, 0.05) * (t_start + i * 0.5))
            for i in range(1, num_periods + 1)
        )
        
        # Forward swap rate
        fwd_swap_rate = (df_start - df_end) / annuity if annuity > 0 else 0.05
        
        # Get swaption volatility
        vol = market_data.volatility_surfaces.get("swaption_vol", {}).get(
            (t_expiry, swap_tenor), 0.15
        )
        if isinstance(vol, dict):
            vol = 0.15
        
        # Discount to expiry
        df_expiry = np.exp(-curve_value(discount_curve, t_expiry, 0.05) * t_expiry)
        
        # Black normal model
        if self.option_type == OptionType.CALL:  # Payer swaption
            option_value = bachelier_call(fwd_swap_rate, self.strike, t_expiry, vol, 1.0)
        else:  # Receiver swaption
            option_value = bachelier_put(fwd_swap_rate, self.strike, t_expiry, vol, 1.0)
        
        npv = self.notional * annuity * option_value * df_expiry
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "forward_swap_rate": fwd_swap_rate,
                "annuity": annuity,
                "option_value_per_notional": option_value,
            },
            greeks={
                "vega": npv * 0.01,
                "delta": norm.cdf((fwd_swap_rate - self.strike) / (vol * np.sqrt(t_expiry))) 
                         if self.option_type == OptionType.CALL else 
                         norm.cdf((fwd_swap_rate - self.strike) / (vol * np.sqrt(t_expiry))) - 1,
            },
            metadata={
                "product_type": self.product_type.value,
                "expiry": self.expiry_date.isoformat(),
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
        
        valuation_date = market_data.valuation_date
        t_expiry = year_fraction(valuation_date, self.expiry_date, DayCountConvention.ACT_365)
        
        horizon = min(time_horizon, t_expiry)
        num_steps = max(int(horizon * 4), 4)
        time_grid = list(np.linspace(0, horizon, num_steps + 1))
        
        # Option time decay
        ee_profile = [
            max(0, current_npv * np.sqrt(max(0, t_expiry - t) / t_expiry))
            for t in time_grid
        ]
        pfe_profile = ee_profile.copy()
        
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=ee_profile,
            peak_exposure=max(pfe_profile),
            epe=np.mean(ee_profile),
            effective_epe=np.mean(ee_profile),
            cva=0.0,
            metadata={"method": "option_decay"}
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """Calculate SA-CCR exposure."""
        result = self.price(market_data)
        rc = max(0, result.npv)
        
        valuation_date = market_data.valuation_date
        t_expiry = year_fraction(valuation_date, self.expiry_date, DayCountConvention.ACT_365)
        swap_tenor = year_fraction(self.effective_date, self.maturity_date, DayCountConvention.ACT_365)
        
        # Supervisory duration (for underlying swap)
        t_start = year_fraction(valuation_date, self.effective_date, DayCountConvention.ACT_365)
        t_end = year_fraction(valuation_date, self.maturity_date, DayCountConvention.ACT_365)
        sd = (np.exp(-0.05 * t_start) - np.exp(-0.05 * t_end)) / 0.05
        
        sf = SACCRParameters.get_supervisory_factor(AssetClass.INTEREST_RATE)
        mf = SACCRParameters.calculate_maturity_factor(t_expiry)
        
        # Option delta
        delta = result.greeks.get("delta", 0.5)
        
        effective_notional = self.notional * sd
        pfe_addon = sf * np.abs(delta) * effective_notional * mf
        
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.INTEREST_RATE,
            metadata={
                "delta": delta,
                "supervisory_duration": sd,
                "swap_tenor": swap_tenor,
            }
        )


# =============================================================================
# Basis Swap
# =============================================================================

class BasisSwap(InterestRateSwap):
    """
    Basis Swap.
    
    Exchange of two different floating rate indices (e.g., 3M LIBOR vs 6M LIBOR,
    or SOFR vs Fed Funds).
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
        index_pay: FloatingRateIndex,
        index_receive: FloatingRateIndex,
        spread_pay: float = 0.0,
        spread_receive: float = 0.0,
        frequency_pay: PaymentFrequency = PaymentFrequency.QUARTERLY,
        frequency_receive: PaymentFrequency = PaymentFrequency.SEMI_ANNUAL,
        **kwargs
    ):
        # Initialize with first index as "floating"
        super().__init__(
            trade_id=trade_id,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            fixed_rate=0.0,  # Not used
            floating_index=index_pay,
            is_payer=True,
            fixed_frequency=frequency_pay,
            float_frequency=frequency_receive,
            **kwargs
        )
        
        self.product_type = ProductType.BASIS_SWAP
        self.index_pay = index_pay
        self.index_receive = index_receive
        self.spread_pay = spread_pay
        self.spread_receive = spread_receive
        self.frequency_pay = frequency_pay
        self.frequency_receive = frequency_receive
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the basis swap."""
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        discount_curve = market_data.discount_curve
        
        # Get forward curves for both indices
        pay_curve = market_data.forward_curves.get(
            self.index_pay.value, discount_curve
        )
        receive_curve = market_data.forward_curves.get(
            self.index_receive.value, discount_curve
        )
        
        # Price pay leg
        pay_schedule = self.generate_schedule(self.frequency_pay)
        pay_pv = 0.0
        
        for start, end in pay_schedule:
            if end <= valuation_date:
                continue
            
            tau = year_fraction(start, end, DayCountConvention.ACT_360)
            t_end = year_fraction(valuation_date, end, DayCountConvention.ACT_365)
            
            df_pay = np.exp(-curve_value(pay_curve, t_end, 0.05) * t_end)
            fwd_rate = curve_value(pay_curve, t_end, 0.05)
            
            df_discount = np.exp(-curve_value(discount_curve, t_end, 0.05) * t_end)
            pay_pv += self.notional * (fwd_rate + self.spread_pay) * tau * df_discount
        
        # Price receive leg
        receive_schedule = self.generate_schedule(self.frequency_receive)
        receive_pv = 0.0
        
        for start, end in receive_schedule:
            if end <= valuation_date:
                continue
            
            tau = year_fraction(start, end, DayCountConvention.ACT_360)
            t_end = year_fraction(valuation_date, end, DayCountConvention.ACT_365)
            
            fwd_rate = curve_value(receive_curve, t_end, 0.05)
            
            df_discount = np.exp(-curve_value(discount_curve, t_end, 0.05) * t_end)
            receive_pv += self.notional * (fwd_rate + self.spread_receive) * tau * df_discount
        
        npv = receive_pv - pay_pv
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "pay_leg_pv": pay_pv,
                "receive_leg_pv": receive_pv,
            },
            greeks={
                "basis_dv01": self.notional * 0.0001,
            },
            metadata={"product_type": self.product_type.value}
        )
