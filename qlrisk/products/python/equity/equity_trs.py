"""
QLRisk - Equity Total Return Swap (TRS) v1.3.0
=============================================================

Equity Total Return Swap implementation with full CCR analytics support.

An Equity Total Return Swap (TRS) is a derivative contract where one party (total 
return payer) pays the total return of an equity asset (price appreciation + dividends)
while receiving a financing rate (typically SOFR/LIBOR + spread) from the counterparty.

Key Features:
- Total return includes price changes and dividends
- Financing leg based on floating rate + spread
- Used for synthetic equity exposure, leverage, and balance sheet optimization
- Can be funded or unfunded

Use Cases:
- Synthetic equity exposure without direct ownership
- Leverage/financing strategies
- Balance sheet optimization
- Tax-efficient equity exposure
- Prime brokerage financing

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

from ...base import (
    BaseProduct, ProductType, AssetClass, Currency,
    DayCountConvention, PaymentFrequency, FloatingRateIndex,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class EquityTRSType(Enum):
    """Type of equity underlying for TRS."""
    SINGLE_STOCK = "single_stock"
    EQUITY_INDEX = "equity_index"
    ETF = "etf"
    BASKET = "basket"
    CUSTOM_INDEX = "custom_index"


class TRSReturnType(Enum):
    """How total return is calculated."""
    TOTAL_RETURN = "total_return"          # Price + dividends
    PRICE_RETURN = "price_return"          # Price only
    EXCESS_RETURN = "excess_return"        # Total return - financing rate


class TRSResetType(Enum):
    """Reset frequency for TRS."""
    BULLET = "bullet"           # Single payment at maturity
    PERIODIC = "periodic"       # Periodic resets
    DAILY = "daily"            # Daily mark-to-market


@dataclass
class EquityTRSTerms:
    """Terms specific to Equity TRS contracts."""
    underlying_type: EquityTRSType = EquityTRSType.SINGLE_STOCK
    underlying_ticker: str = ""
    underlying_name: str = ""
    initial_price: float = 0.0
    current_price: float = 0.0
    dividend_yield: float = 0.0
    return_type: TRSReturnType = TRSReturnType.TOTAL_RETURN
    reset_type: TRSResetType = TRSResetType.PERIODIC
    financing_index: FloatingRateIndex = FloatingRateIndex.SOFR
    financing_spread: float = 0.0  # Spread over floating rate (bps)
    is_funded: bool = True
    initial_margin: float = 0.0
    variation_margin: float = 0.0
    collateral_currency: Currency = Currency.USD


class EquityTRS(BaseProduct):
    """
    Equity Total Return Swap (TRS).
    
    A derivative where one party pays the total return of an equity asset
    (including price appreciation and dividends) in exchange for a financing
    payment (floating rate + spread).
    
    Total Return Payer receives:
        Financing Rate = Notional × (SOFR + Spread) × Δt
    
    Total Return Payer pays:
        Total Return = Notional × (P_t/P_0 - 1) + Dividends
    
    Key CCR Characteristics:
    - Exposure profile similar to equity swap
    - Dividend risk adds to exposure volatility
    - Financing spread affects break-even
    - SA-CCR: Equity asset class, 32% SF for single name, 20% for index
    
    Example:
        trs = EquityTRS(
            trade_id="EQ-TRS-001",
            trade_date=date.today(),
            effective_date=date.today(),
            maturity_date=date(2025, 12, 31),
            notional=10_000_000,
            currency=Currency.USD,
            counterparty_id="CPTY-001",
            terms=EquityTRSTerms(
                underlying_type=EquityTRSType.SINGLE_STOCK,
                underlying_ticker="AAPL",
                initial_price=180.0,
                financing_spread=50  # 50 bps over SOFR
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
        terms: Optional[EquityTRSTerms] = None,
        is_receiver: bool = True,  # True = receive total return, pay financing
        payment_frequency: PaymentFrequency = PaymentFrequency.QUARTERLY,
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.EQUITY_TRS,
            asset_class=AssetClass.EQUITY,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.terms = terms or EquityTRSTerms()
        self.is_receiver = is_receiver  # Receive total return
        self.payment_frequency = payment_frequency
        self.day_count = day_count
        
    def get_underlying_return(self, market_data: MarketData) -> float:
        """
        Calculate the total return of the underlying equity.
        
        Returns:
            Total return as a decimal (e.g., 0.10 for 10%)
        """
        if self.terms.initial_price <= 0:
            return 0.0
            
        current_price = self.terms.current_price or self.terms.initial_price
        price_return = (current_price / self.terms.initial_price) - 1.0
        
        if self.terms.return_type == TRSReturnType.PRICE_RETURN:
            return price_return
        
        # Add dividend yield for total return
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        elapsed = max(0, year_fraction(self.effective_date, market_data.valuation_date, self.day_count))
        dividend_return = self.terms.dividend_yield * elapsed
        
        total_return = price_return + dividend_return
        
        if self.terms.return_type == TRSReturnType.EXCESS_RETURN:
            # Subtract financing cost
            financing_rate = getattr(market_data, 'sofr_rate', 0.05) + self.terms.financing_spread / 10000
            total_return -= financing_rate * elapsed
            
        return total_return
    
    def price(self, market_data: MarketData) -> PricingResult:
        """
        Price the Equity TRS.
        
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
        df = np.exp(-discount_curve.get(remaining, 0.05) * remaining)
        
        # Calculate equity return
        total_return = self.get_underlying_return(market_data)
        equity_leg = self.notional * total_return
        
        # Calculate financing leg
        financing_rate = getattr(market_data, 'sofr_rate', 0.05) + self.terms.financing_spread / 10000
        financing_leg = self.notional * financing_rate * elapsed
        
        # Direction: receiver of total return pays financing
        direction = 1.0 if self.is_receiver else -1.0
        npv = direction * (equity_leg - financing_leg) * df
        
        # Greeks
        delta = self.notional / self.terms.initial_price if self.terms.initial_price > 0 else 0
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "equity_leg": equity_leg,
                "financing_leg": financing_leg,
                "total_return": total_return,
                "remaining_maturity": remaining,
                "elapsed_time": elapsed
            },
            greeks={
                "delta": delta * direction,
                "equity_exposure": self.notional * direction,
                "financing_dv01": self.notional * elapsed * 0.0001
            },
            metadata={
                "product_type": "equity_trs",
                "underlying": self.terms.underlying_ticker,
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
        Calculate CCR exposure profile for the Equity TRS.
        
        Equity TRS has significant directional exposure to the underlying,
        with additional risk from dividend uncertainty.
        
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
        
        # Equity volatility for exposure simulation
        equity_vol = getattr(market_data, 'equity_volatility', 0.25)
        
        # Expected exposure increases with volatility, decreases as maturity approaches
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            time_to_end = max(0, remaining - t)
            if time_to_end <= 0:
                ee_profile.append(0.0)
                pfe_profile.append(0.0)
                continue
            
            # EE grows with sqrt(t) due to diffusion
            vol_factor = equity_vol * np.sqrt(t) if t > 0 else 0
            drift_factor = self.terms.dividend_yield * t
            
            # Base exposure with directional component
            base_ee = current_exposure * (1 + vol_factor) * (time_to_end / remaining if remaining > 0 else 1)
            base_ee += abs(self.notional) * vol_factor * 0.4  # Vol contribution
            
            ee_profile.append(max(0, base_ee))
            
            # PFE at confidence level
            z_score = 1.645 if confidence_level == 0.95 else 2.326
            pfe = base_ee + abs(self.notional) * equity_vol * np.sqrt(t) * z_score
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
        
        # Simple CVA approximation
        pd = 0.02  # Assume 2% annual PD
        lgd = 0.60  # 60% LGD
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
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """
        Calculate SA-CCR exposure for the Equity TRS.
        
        For equity TRS:
        - Asset class: Equity
        - Supervisory factor: 32% (single name), 20% (index)
        - Delta: +1 for long, -1 for short
        
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
        
        # Supervisory factor based on underlying type
        if self.terms.underlying_type in [EquityTRSType.EQUITY_INDEX, EquityTRSType.ETF]:
            sf = 0.20  # Index: 20%
        else:
            sf = 0.32  # Single name: 32%
        
        # Maturity factor
        mf = SACCRParameters.calculate_maturity_factor(remaining)
        
        # Delta
        delta = 1.0 if self.is_receiver else -1.0
        
        # Adjusted notional
        adjusted_notional = abs(self.notional) * delta
        
        # PFE Add-on
        pfe_addon = sf * abs(adjusted_notional) * mf
        
        # EAD
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.EQUITY,
            details={
                "supervisory_factor": sf,
                "maturity_factor": mf,
                "delta": delta,
                "adjusted_notional": adjusted_notional,
                "underlying_type": self.terms.underlying_type.value
            }
        )
    
    def get_dividend_dates(self) -> List[date]:
        """Get expected dividend payment dates."""
        # Simplified: quarterly dividends
        dates = []
        current = self.effective_date
        while current < self.maturity_date:
            current = date(
                current.year + (current.month + 3 - 1) // 12,
                (current.month + 3 - 1) % 12 + 1,
                min(current.day, 28)
            )
            if current <= self.maturity_date:
                dates.append(current)
        return dates
    
    def __repr__(self) -> str:
        return (
            f"EquityTRS(trade_id='{self.trade_id}', "
            f"underlying='{self.terms.underlying_ticker}', "
            f"notional={self.notional:,.0f}, "
            f"receiver={self.is_receiver})"
        )


__all__ = [
    "EquityTRS",
    "EquityTRSType",
    "EquityTRSTerms",
    "TRSReturnType",
    "TRSResetType",
]
