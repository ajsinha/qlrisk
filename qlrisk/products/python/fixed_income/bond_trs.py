"""
QLRisk - Bond Total Return Swap (TRS) v2.2.1
============================================================

Bond Total Return Swap implementation with full CCR analytics support.

A Bond Total Return Swap (TRS) is a derivative contract where one party (total 
return payer) pays the total return of a bond or bond portfolio (price changes,
coupon payments, and any principal changes) while receiving a financing rate 
(typically SOFR/LIBOR + spread) from the counterparty.

Key Features:
- Total return includes price changes, accrued interest, and coupon payments
- Financing leg based on floating rate + spread
- Used for synthetic bond exposure, leverage, and balance sheet optimization
- Common in credit trading and structured finance

Use Cases:
- Synthetic bond/credit exposure without direct ownership
- Leverage/financing strategies
- Balance sheet optimization (off-balance sheet financing)
- Regulatory capital optimization
- Credit spread trading
- CLO/ABS portfolio exposure

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from datetime import date
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
import numpy as np

from ...base import curve_value
from ...base import (
    BaseProduct, ProductType, AssetClass, Currency,
    DayCountConvention, PaymentFrequency, FloatingRateIndex,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class BondTRSUnderlyingType(Enum):
    """Type of bond underlying for TRS."""
    SINGLE_BOND = "single_bond"
    BOND_INDEX = "bond_index"
    BOND_PORTFOLIO = "bond_portfolio"
    GOVERNMENT_BOND = "government_bond"
    CORPORATE_BOND = "corporate_bond"
    HIGH_YIELD_BOND = "high_yield_bond"
    INVESTMENT_GRADE = "investment_grade"
    EMERGING_MARKET = "emerging_market"
    MBS = "mbs"
    ABS = "abs"
    CLO = "clo"
    CDO = "cdo"


class BondTRSReturnType(Enum):
    """How total return is calculated."""
    TOTAL_RETURN = "total_return"          # Price + coupons + accrued
    PRICE_RETURN = "price_return"          # Price only
    EXCESS_RETURN = "excess_return"        # Total return - financing rate
    CLEAN_PRICE = "clean_price"            # Clean price only


class BondTRSResetType(Enum):
    """Reset frequency for TRS."""
    BULLET = "bullet"           # Single payment at maturity
    PERIODIC = "periodic"       # Periodic resets
    MONTHLY = "monthly"         # Monthly mark-to-market


@dataclass
class BondTRSTerms:
    """Terms specific to Bond TRS contracts."""
    underlying_type: BondTRSUnderlyingType = BondTRSUnderlyingType.CORPORATE_BOND
    underlying_identifier: str = ""        # ISIN, CUSIP, or index name
    underlying_name: str = ""
    issuer: str = ""
    initial_price: float = 100.0           # As % of face value
    current_price: float = 100.0
    coupon_rate: float = 0.0               # Annual coupon rate
    coupon_frequency: PaymentFrequency = PaymentFrequency.SEMI_ANNUAL
    credit_rating: str = "BBB"
    spread_over_benchmark: float = 0.0     # bps
    modified_duration: float = 5.0
    dv01: float = 0.0
    return_type: BondTRSReturnType = BondTRSReturnType.TOTAL_RETURN
    reset_type: BondTRSResetType = BondTRSResetType.PERIODIC
    financing_index: FloatingRateIndex = FloatingRateIndex.SOFR
    financing_spread: float = 0.0          # Spread over floating rate (bps)
    is_funded: bool = True
    initial_margin: float = 0.0
    variation_margin: float = 0.0
    collateral_currency: Currency = Currency.USD
    # Credit features
    has_credit_event_protection: bool = False
    recovery_rate: float = 0.40


class BondTRS(BaseProduct):
    """
    Bond Total Return Swap (TRS).
    
    A derivative where one party pays the total return of a bond or bond portfolio
    (including price appreciation, coupon payments, and accrued interest) in 
    exchange for a financing payment (floating rate + spread).
    
    Total Return Payer receives:
        Financing Rate = Notional × (SOFR + Spread) × Δt
    
    Total Return Payer pays:
        Total Return = Notional × [(P_t/P_0 - 1) + Coupons + Accrued]
    
    Key CCR Characteristics:
    - Exposure profile influenced by interest rate and credit spread movements
    - Duration and convexity affect exposure sensitivity
    - SA-CCR: Credit asset class for corporate bonds, Interest Rate for govvies
    - Supervisory factors vary by credit quality
    
    Example:
        trs = BondTRS(
            trade_id="BOND-TRS-001",
            trade_date=date.today(),
            effective_date=date.today(),
            maturity_date=date(2026, 12, 31),
            notional=50_000_000,
            currency=Currency.USD,
            counterparty_id="CPTY-001",
            terms=BondTRSTerms(
                underlying_type=BondTRSUnderlyingType.CORPORATE_BOND,
                underlying_identifier="US123456789",
                issuer="ABC Corp",
                initial_price=98.5,
                coupon_rate=0.05,
                credit_rating="BBB",
                financing_spread=75  # 75 bps over SOFR
            )
        )
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
        terms: Optional[BondTRSTerms] = None,
        is_receiver: bool = True,  # True = receive total return, pay financing
        payment_frequency: PaymentFrequency = PaymentFrequency.QUARTERLY,
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        **kwargs
    ):
        # Determine asset class based on underlying
        underlying_type = (terms.underlying_type if terms else 
                          BondTRSUnderlyingType.CORPORATE_BOND)
        
        if underlying_type == BondTRSUnderlyingType.GOVERNMENT_BOND:
            asset_class = AssetClass.INTEREST_RATE
        else:
            asset_class = AssetClass.CREDIT
        
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.BOND_TRS,
            asset_class=asset_class,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.terms = terms or BondTRSTerms()
        self.is_receiver = is_receiver  # Receive total return
        self.payment_frequency = payment_frequency
        self.day_count = day_count
        
    def get_accrued_interest(self, valuation_date: date) -> float:
        """
        Calculate accrued interest on the underlying bond.
        
        Args:
            valuation_date: Valuation date
            
        Returns:
            Accrued interest as % of notional
        """
        if self.terms.coupon_rate <= 0:
            return 0.0
        
        # Simplified: assume last coupon was at effective_date
        days_accrued = (valuation_date - self.effective_date).days
        
        # Days in coupon period based on frequency
        if self.terms.coupon_frequency == PaymentFrequency.ANNUAL:
            days_in_period = 365
        elif self.terms.coupon_frequency == PaymentFrequency.SEMI_ANNUAL:
            days_in_period = 182.5
        elif self.terms.coupon_frequency == PaymentFrequency.QUARTERLY:
            days_in_period = 91.25
        else:
            days_in_period = 30.4  # Monthly
        
        # Accrued interest
        accrued = self.terms.coupon_rate * (days_accrued % days_in_period) / 365
        
        return accrued

    def get_underlying_return(self, market_data: MarketData) -> float:
        """
        Calculate the total return of the underlying bond.
        
        Returns:
            Total return as a decimal (e.g., 0.05 for 5%)
        """
        if self.terms.initial_price <= 0:
            return 0.0
        
        current_price = self.terms.current_price or self.terms.initial_price
        price_return = (current_price / self.terms.initial_price) - 1.0
        
        if self.terms.return_type == BondTRSReturnType.PRICE_RETURN:
            return price_return
        
        if self.terms.return_type == BondTRSReturnType.CLEAN_PRICE:
            return price_return
        
        # Add coupon income for total return
        elapsed = year_fraction(self.effective_date, market_data.valuation_date, self.day_count)
        coupon_return = self.terms.coupon_rate * elapsed
        
        # Add accrued interest
        accrued = self.get_accrued_interest(market_data.valuation_date)
        
        total_return = price_return + coupon_return + accrued
        
        if self.terms.return_type == BondTRSReturnType.EXCESS_RETURN:
            # Subtract financing cost
            financing_rate = getattr(market_data, 'sofr_rate', 0.05) + self.terms.financing_spread / 10000
            total_return -= financing_rate * elapsed
        
        return total_return
    
    def price(self, market_data: MarketData) -> PricingResult:
        """
        Price the Bond TRS.
        
        NPV = Notional × (Total Return - Financing Cost) × Direction
        
        Args:
            market_data: Current market data
            
        Returns:
            PricingResult with NPV and components
        """
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        remaining = self.get_remaining_maturity(valuation_date)
        elapsed = year_fraction(self.effective_date, valuation_date, self.day_count)
        
        # Get discount factor
        discount_curve = market_data.discount_curve
        df = np.exp(-curve_value(discount_curve, remaining, 0.05) * remaining)
        
        # Calculate bond return
        total_return = self.get_underlying_return(market_data)
        bond_leg = self.notional * total_return
        
        # Calculate financing leg
        financing_rate = getattr(market_data, 'sofr_rate', 0.05) + self.terms.financing_spread / 10000
        financing_leg = self.notional * financing_rate * elapsed
        
        # Direction: receiver of total return pays financing
        direction = 1.0 if self.is_receiver else -1.0
        npv = direction * (bond_leg - financing_leg) * df
        
        # Greeks
        dv01 = self.terms.dv01 if self.terms.dv01 > 0 else (
            self.notional * self.terms.modified_duration * 0.0001
        )
        cs01 = self.notional * self.terms.modified_duration * 0.0001  # Credit spread sensitivity
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "bond_leg": bond_leg,
                "financing_leg": financing_leg,
                "total_return": total_return,
                "accrued_interest": self.get_accrued_interest(valuation_date),
                "remaining_maturity": remaining,
                "elapsed_time": elapsed,
                "current_price": self.terms.current_price,
                "initial_price": self.terms.initial_price
            },
            greeks={
                "dv01": dv01 * direction,
                "cs01": cs01 * direction,
                "duration": self.terms.modified_duration,
                "notional_exposure": self.notional * direction
            },
            metadata={
                "product_type": "bond_trs",
                "underlying": self.terms.underlying_identifier,
                "underlying_type": self.terms.underlying_type.value,
                "issuer": self.terms.issuer,
                "credit_rating": self.terms.credit_rating,
                "is_receiver": self.is_receiver
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """
        Calculate CCR exposure profile for the Bond TRS.
        
        Bond TRS has exposure to both interest rate and credit spread movements.
        Duration and credit rating significantly impact the exposure profile.
        
        Args:
            market_data: Current market data
            time_horizon: Time horizon in years
            num_scenarios: Number of Monte Carlo scenarios
            confidence_level: Confidence level for PFE
            
        Returns:
            CCRExposureProfile with exposure metrics
        """
        result = self.price(market_data)
        current_exposure = max(0, result.npv)
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining) if remaining > 0 else time_horizon
        
        # Time grid
        num_points = 20
        time_grid = list(np.linspace(0, max(0.1, horizon), num_points))
        
        # Volatility factors
        rate_vol = 0.01  # Interest rate volatility
        spread_vol = self._get_spread_volatility()  # Credit spread volatility
        
        # Combined volatility considering duration
        combined_vol = np.sqrt(
            (rate_vol * self.terms.modified_duration) ** 2 +
            (spread_vol * self.terms.modified_duration) ** 2
        )
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            time_to_end = max(0, remaining - t)
            if time_to_end <= 0:
                ee_profile.append(0.0)
                pfe_profile.append(0.0)
                continue
            
            # EE grows with sqrt(t) due to diffusion
            vol_factor = combined_vol * np.sqrt(t) if t > 0 else 0
            
            # Base exposure
            base_ee = current_exposure * (1 + vol_factor) * (time_to_end / remaining if remaining > 0 else 1)
            base_ee += abs(self.notional) * vol_factor * 0.3
            
            # Add coupon carry benefit for receiver
            if self.is_receiver:
                coupon_benefit = self.notional * self.terms.coupon_rate * t * 0.5
                base_ee = max(0, base_ee - coupon_benefit * 0.3)
            
            ee_profile.append(max(0, base_ee))
            
            # PFE at confidence level
            z_score = 1.645 if confidence_level == 0.95 else 2.326
            pfe = base_ee + abs(self.notional) * combined_vol * np.sqrt(t) * z_score
            pfe_profile.append(max(0, pfe))
        
        # Effective EE (non-decreasing)
        effective_ee = []
        max_ee = 0
        for ee in ee_profile:
            max_ee = max(max_ee, ee)
            effective_ee.append(max_ee)
        
        # Calculate aggregates
        peak_exposure = max(pfe_profile) if pfe_profile else 0
        epe = np.mean(ee_profile) if ee_profile else 0
        effective_epe = np.mean(effective_ee) if effective_ee else 0
        
        # CVA calculation
        pd = self._get_pd_from_rating()
        lgd = 1.0 - self.terms.recovery_rate
        cva = effective_epe * pd * lgd * horizon
        
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=effective_ee,
            peak_exposure=peak_exposure,
            epe=epe,
            effective_epe=effective_epe,
            cva=cva
        )
    
    def _get_spread_volatility(self) -> float:
        """Get credit spread volatility based on rating."""
        vol_map = {
            "AAA": 0.002, "AA+": 0.003, "AA": 0.004, "AA-": 0.005,
            "A+": 0.006, "A": 0.008, "A-": 0.010,
            "BBB+": 0.012, "BBB": 0.015, "BBB-": 0.020,
            "BB+": 0.030, "BB": 0.040, "BB-": 0.050,
            "B+": 0.060, "B": 0.080, "B-": 0.100,
            "CCC": 0.150, "CC": 0.200, "C": 0.250
        }
        return vol_map.get(self.terms.credit_rating.upper(), 0.02)
    
    def _get_pd_from_rating(self) -> float:
        """Get annual PD based on credit rating."""
        pd_map = {
            "AAA": 0.0001, "AA+": 0.0002, "AA": 0.0003, "AA-": 0.0005,
            "A+": 0.0008, "A": 0.0010, "A-": 0.0015,
            "BBB+": 0.0025, "BBB": 0.0040, "BBB-": 0.0070,
            "BB+": 0.0100, "BB": 0.0150, "BB-": 0.0250,
            "B+": 0.0400, "B": 0.0600, "B-": 0.1000,
            "CCC": 0.1500, "CC": 0.2500, "C": 0.3500
        }
        return pd_map.get(self.terms.credit_rating.upper(), 0.02)
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """
        Calculate SA-CCR exposure for the Bond TRS.
        
        For bond TRS:
        - Asset class: Credit (corporate) or Interest Rate (government)
        - Supervisory factor varies by credit quality
        - Duration-weighted notional for interest rate component
        
        EAD = α × (RC + PFE)
        
        Args:
            market_data: Current market data
            
        Returns:
            SACCRExposure with regulatory capital components
        """
        result = self.price(market_data)
        
        # Replacement Cost
        rc = max(0, result.npv)
        
        # Remaining maturity
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        
        # Supervisory factor based on credit quality
        sf = self._get_saccr_sf()
        
        # Maturity factor
        mf = SACCRParameters.calculate_maturity_factor(remaining)
        
        # Delta
        delta = 1.0 if self.is_receiver else -1.0
        
        # Adjusted notional (duration-weighted for rate risk)
        duration = self.terms.modified_duration
        adjusted_notional = abs(self.notional) * duration / 5.0  # Normalize to 5Y
        
        # PFE Add-on
        pfe_addon = sf * abs(adjusted_notional) * mf
        
        # EAD
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=self.asset_class,
            metadata={
                "supervisory_factor": sf,
                "maturity_factor": mf,
                "delta": delta,
                "adjusted_notional": adjusted_notional,
                "duration": duration,
                "credit_rating": self.terms.credit_rating,
                "underlying_type": self.terms.underlying_type.value
            }
        )
    
    def _get_saccr_sf(self) -> float:
        """Get SA-CCR supervisory factor based on credit quality."""
        rating = self.terms.credit_rating.upper()
        
        if self.terms.underlying_type == BondTRSUnderlyingType.GOVERNMENT_BOND:
            return 0.005  # 0.5% for government bonds (IR asset class)
        
        # Credit asset class supervisory factors
        if rating in ["AAA", "AA+", "AA", "AA-"]:
            return 0.0038  # 0.38% for AAA-AA
        elif rating in ["A+", "A", "A-"]:
            return 0.0042  # 0.42% for A
        elif rating in ["BBB+", "BBB", "BBB-"]:
            return 0.0054  # 0.54% for BBB
        elif rating in ["BB+", "BB", "BB-"]:
            return 0.0106  # 1.06% for BB
        elif rating in ["B+", "B", "B-"]:
            return 0.0160  # 1.60% for B
        else:
            return 0.0600  # 6.0% for CCC and below
    
    def get_coupon_dates(self) -> List[date]:
        """Get expected coupon payment dates."""
        dates = []
        current = self.effective_date
        
        # Months between payments
        if self.terms.coupon_frequency == PaymentFrequency.ANNUAL:
            months = 12
        elif self.terms.coupon_frequency == PaymentFrequency.SEMI_ANNUAL:
            months = 6
        elif self.terms.coupon_frequency == PaymentFrequency.QUARTERLY:
            months = 3
        else:
            months = 1
        
        while current < self.maturity_date:
            new_month = current.month + months
            new_year = current.year + (new_month - 1) // 12
            new_month = (new_month - 1) % 12 + 1
            current = date(new_year, new_month, min(current.day, 28))
            if current <= self.maturity_date:
                dates.append(current)
        
        return dates
    
    def __repr__(self) -> str:
        return (
            f"BondTRS(trade_id='{self.trade_id}', "
            f"underlying='{self.terms.underlying_identifier}', "
            f"notional={self.notional:,.0f}, "
            f"rating={self.terms.credit_rating}, "
            f"receiver={self.is_receiver})"
        )


__all__ = [
    "BondTRS",
    "BondTRSUnderlyingType",
    "BondTRSTerms",
    "BondTRSReturnType",
    "BondTRSResetType",
]
