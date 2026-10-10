"""
QLRisk - Prime Brokerage Agreement v2.0.1
=========================================================

Prime Brokerage agreement implementation with full CCR analytics support.

A Prime Brokerage Agreement is a bundled package of services provided by 
investment banks to hedge funds and institutional clients, including:
- Securities lending
- Margin financing
- Trade execution and clearing
- Custody services
- Reporting and technology

Key Features:
- Multi-product financing arrangement
- Cross-margining across positions
- Dynamic collateral management
- Rehypothecation rights

Use Cases:
- Hedge fund prime brokerage
- Institutional securities financing
- Cross-product margin optimization
- Portfolio-level risk management

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from datetime import date
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import numpy as np

from ...base import (
    BaseProduct, ProductType, AssetClass, Currency,
    DayCountConvention, PaymentFrequency, FloatingRateIndex,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class PBServiceType(Enum):
    """Types of prime brokerage services."""
    SECURITIES_LENDING = "securities_lending"
    MARGIN_FINANCING = "margin_financing"
    SYNTHETIC_FINANCING = "synthetic_financing"
    CUSTODY = "custody"
    TRADE_EXECUTION = "trade_execution"
    CLEARING = "clearing"
    REPORTING = "reporting"
    FULL_SERVICE = "full_service"


class PBAccountType(Enum):
    """Type of prime brokerage account."""
    MARGIN = "margin"
    CASH = "cash"
    SHORT = "short"
    CUSTODY = "custody"


class PBCollateralType(Enum):
    """Types of collateral accepted in PB."""
    CASH = "cash"
    GOVERNMENT_BONDS = "government_bonds"
    INVESTMENT_GRADE_BONDS = "investment_grade_bonds"
    EQUITIES = "equities"
    ETF = "etf"
    MONEY_MARKET = "money_market"


@dataclass
class PBPosition:
    """A position within the prime brokerage account."""
    security_id: str
    security_type: str
    quantity: float
    market_value: float
    haircut: float = 0.0
    is_long: bool = True
    is_rehypothecatable: bool = True


@dataclass
class PrimeBrokerageTerms:
    """Terms specific to Prime Brokerage agreements."""
    service_types: List[PBServiceType] = field(default_factory=lambda: [PBServiceType.FULL_SERVICE])
    account_type: PBAccountType = PBAccountType.MARGIN
    
    # Financing terms
    financing_rate_spread: float = 50.0  # bps over benchmark
    short_rebate_spread: float = -25.0   # bps (negative = cost)
    benchmark_rate: FloatingRateIndex = FloatingRateIndex.SOFR
    
    # Margin requirements
    initial_margin_requirement: float = 0.50  # 50% Reg T
    maintenance_margin: float = 0.25          # 25%
    house_margin_excess: float = 0.05         # Additional house requirement
    
    # Collateral
    accepted_collateral: List[PBCollateralType] = field(
        default_factory=lambda: [PBCollateralType.CASH, PBCollateralType.GOVERNMENT_BONDS]
    )
    
    # Positions
    positions: List[PBPosition] = field(default_factory=list)
    
    # Limits
    gross_exposure_limit: float = 0.0
    net_exposure_limit: float = 0.0
    concentration_limit: float = 0.10  # Max 10% in single security
    
    # Rehypothecation
    rehypothecation_allowed: bool = True
    rehypothecation_limit: float = 1.40  # 140% of debit balance
    
    # Fees
    custody_fee_bps: float = 5.0
    execution_fee_bps: float = 2.0


class PrimeBrokerage(BaseProduct):
    """
    Prime Brokerage Agreement.
    
    A comprehensive financing arrangement providing bundled services including
    securities lending, margin financing, trade execution, clearing, and custody.
    
    The agreement acts as a master facility under which multiple positions and
    financing arrangements are managed with cross-margining benefits.
    
    Key CCR Characteristics:
    - Portfolio-level netting
    - Dynamic margin requirements
    - Multiple asset class exposures
    - Rehypothecation considerations
    
    Example:
        pb = PrimeBrokerage(
            trade_id="PB-001",
            trade_date=date.today(),
            effective_date=date.today(),
            maturity_date=date(2025, 12, 31),
            notional=100_000_000,  # Credit line
            currency=Currency.USD,
            counterparty_id="HEDGE-FUND-001",
            terms=PrimeBrokerageTerms(
                service_types=[PBServiceType.FULL_SERVICE],
                financing_rate_spread=40,
                initial_margin_requirement=0.50
            )
        )
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,  # Credit facility size
        currency: Currency,
        counterparty_id: str,
        terms: Optional[PrimeBrokerageTerms] = None,
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.PRIME_BROKERAGE,
            asset_class=AssetClass.EQUITY,  # Primary asset class
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.terms = terms or PrimeBrokerageTerms()
        self.day_count = day_count
    
    def get_gross_market_value(self) -> float:
        """Calculate gross market value of all positions."""
        return sum(abs(p.market_value) for p in self.terms.positions)
    
    def get_net_market_value(self) -> float:
        """Calculate net market value of all positions."""
        return sum(
            p.market_value if p.is_long else -p.market_value 
            for p in self.terms.positions
        )
    
    def get_long_market_value(self) -> float:
        """Calculate total long market value."""
        return sum(p.market_value for p in self.terms.positions if p.is_long)
    
    def get_short_market_value(self) -> float:
        """Calculate total short market value."""
        return sum(p.market_value for p in self.terms.positions if not p.is_long)
    
    def get_collateral_value(self) -> float:
        """Calculate haircut-adjusted collateral value."""
        return sum(
            p.market_value * (1 - p.haircut) 
            for p in self.terms.positions
        )
    
    def get_margin_requirement(self) -> float:
        """Calculate total margin requirement."""
        long_value = self.get_long_market_value()
        short_value = self.get_short_market_value()
        
        # Reg T margin: 50% of long + 50% of short
        reg_t_margin = (
            long_value * self.terms.initial_margin_requirement +
            short_value * self.terms.initial_margin_requirement
        )
        
        # House margin excess
        house_margin = self.get_gross_market_value() * self.terms.house_margin_excess
        
        return reg_t_margin + house_margin
    
    def get_financing_cost(self, market_data: MarketData) -> float:
        """Calculate financing costs/income."""
        elapsed = year_fraction(
            self.effective_date, 
            market_data.valuation_date, 
            self.day_count
        )
        
        benchmark = getattr(market_data, 'sofr_rate', 0.05)
        
        # Long financing cost
        long_value = self.get_long_market_value()
        long_cost = long_value * (benchmark + self.terms.financing_rate_spread / 10000) * elapsed
        
        # Short rebate (typically negative = cost)
        short_value = self.get_short_market_value()
        short_rebate = short_value * (benchmark + self.terms.short_rebate_spread / 10000) * elapsed
        
        return long_cost - short_rebate
    
    def price(self, market_data: MarketData) -> PricingResult:
        """
        Price the Prime Brokerage position.
        
        The NPV represents the net financing value considering:
        - Net position value
        - Financing costs
        - Margin excess/deficit
        
        Args:
            market_data: Current market data
            
        Returns:
            PricingResult with NPV and components
        """
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        # Position values
        gross_value = self.get_gross_market_value()
        net_value = self.get_net_market_value()
        long_value = self.get_long_market_value()
        short_value = self.get_short_market_value()
        
        # Margin
        margin_required = self.get_margin_requirement()
        collateral_value = self.get_collateral_value()
        margin_excess = collateral_value - margin_required
        
        # Financing
        financing_cost = self.get_financing_cost(market_data)
        
        # Fees
        remaining = self.get_remaining_maturity(valuation_date)
        elapsed = year_fraction(self.effective_date, valuation_date, self.day_count)
        custody_fee = gross_value * (self.terms.custody_fee_bps / 10000) * elapsed
        
        # NPV from client perspective
        npv = net_value - financing_cost - custody_fee
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "gross_market_value": gross_value,
                "net_market_value": net_value,
                "long_market_value": long_value,
                "short_market_value": short_value,
                "margin_required": margin_required,
                "collateral_value": collateral_value,
                "margin_excess": margin_excess,
                "financing_cost": financing_cost,
                "custody_fee": custody_fee,
                "num_positions": len(self.terms.positions)
            },
            greeks={
                "delta": 1.0,  # Direct exposure
                "financing_sensitivity": long_value * 0.0001 * elapsed
            },
            metadata={
                "product_type": "prime_brokerage",
                "service_types": [s.value for s in self.terms.service_types],
                "account_type": self.terms.account_type.value
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
        Calculate CCR exposure profile for the Prime Brokerage.
        
        PB exposure depends on:
        - Net position exposure
        - Potential margin deficit
        - Rehypothecation exposure
        """
        result = self.price(market_data)
        
        gross_value = self.get_gross_market_value()
        net_value = abs(self.get_net_market_value())
        current_exposure = max(0, result.npv)
        
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining) if remaining > 0 else time_horizon
        
        # Time grid
        num_points = 20
        time_grid = list(np.linspace(0, max(0.1, horizon), num_points))
        
        # Portfolio volatility (simplified)
        portfolio_vol = 0.20  # Assumed equity-like vol
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            time_to_end = max(0, remaining - t)
            if time_to_end <= 0:
                ee_profile.append(0.0)
                pfe_profile.append(0.0)
                continue
            
            # Exposure scales with gross value and volatility
            vol_factor = portfolio_vol * np.sqrt(t) if t > 0 else 0
            
            # Base expected exposure
            base_ee = current_exposure + gross_value * vol_factor * 0.2
            
            # Add potential margin call exposure
            margin_exposure = self.get_margin_requirement() * vol_factor * 0.5
            
            ee_profile.append(max(0, base_ee + margin_exposure))
            
            # PFE
            z_score = 1.645 if confidence_level == 0.95 else 2.326
            pfe = base_ee + gross_value * portfolio_vol * np.sqrt(t) * z_score
            pfe_profile.append(max(0, pfe))
        
        # Effective EE
        effective_ee = []
        max_ee = 0
        for ee in ee_profile:
            max_ee = max(max_ee, ee)
            effective_ee.append(max_ee)
        
        peak_exposure = max(pfe_profile) if pfe_profile else 0
        epe = np.mean(ee_profile) if ee_profile else 0
        effective_epe = np.mean(effective_ee) if effective_ee else 0
        
        # CVA
        pd = 0.02
        lgd = 0.60
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
        Calculate SA-CCR exposure for Prime Brokerage.
        
        PB is treated as SFT under SA-CCR with specific haircuts
        and netting considerations.
        """
        result = self.price(market_data)
        
        rc = max(0, result.npv)
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        
        # Use equity SF for the primary exposure
        sf = 0.32  # Single equity SF
        mf = SACCRParameters.calculate_maturity_factor(remaining)
        
        # Net exposure for add-on
        net_exposure = abs(self.get_net_market_value())
        pfe_addon = sf * net_exposure * mf
        
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.EQUITY,
            details={
                "supervisory_factor": sf,
                "maturity_factor": mf,
                "gross_exposure": self.get_gross_market_value(),
                "net_exposure": net_exposure,
                "num_positions": len(self.terms.positions)
            }
        )
    
    def add_position(self, position: PBPosition) -> None:
        """Add a position to the prime brokerage account."""
        self.terms.positions.append(position)
    
    def __repr__(self) -> str:
        return (
            f"PrimeBrokerage(trade_id='{self.trade_id}', "
            f"facility={self.notional:,.0f}, "
            f"positions={len(self.terms.positions)}, "
            f"gross={self.get_gross_market_value():,.0f})"
        )


__all__ = [
    "PrimeBrokerage",
    "PrimeBrokerageTerms",
    "PBServiceType",
    "PBAccountType",
    "PBCollateralType",
    "PBPosition",
]
