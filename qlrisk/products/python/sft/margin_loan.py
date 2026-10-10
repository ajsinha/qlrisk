"""
QLRisk - Margin Loan v2.3.1
==========================================

Margin Loan (securities-based lending) implementation with full CCR analytics.

A Margin Loan is a loan secured by marketable securities where the borrower
pledges securities as collateral. The loan amount is typically a percentage
of the collateral value (loan-to-value ratio).

Key Features:
- Collateralized lending against securities
- Daily mark-to-market and margin calls
- Haircuts based on collateral type
- Rehypothecation rights

Use Cases:
- Client leverage for investment
- Prime brokerage financing
- Securities-backed credit facilities
- Wealth management lending

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


class MarginLoanType(Enum):
    """Type of margin loan."""
    PORTFOLIO_MARGIN = "portfolio_margin"
    REG_T_MARGIN = "reg_t_margin"           # Regulation T (50% initial)
    SECURITIES_BACKED = "securities_backed"  # General purpose
    CONCENTRATED = "concentrated"            # Single stock concentrated
    PLEDGED_ASSET = "pledged_asset"         # Pledged asset line


class CollateralCategory(Enum):
    """Categories of collateral for haircut determination."""
    CASH = "cash"
    GOVERNMENT_BONDS = "government_bonds"
    INVESTMENT_GRADE = "investment_grade"
    HIGH_YIELD = "high_yield"
    LARGE_CAP_EQUITY = "large_cap_equity"
    MID_CAP_EQUITY = "mid_cap_equity"
    SMALL_CAP_EQUITY = "small_cap_equity"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    RESTRICTED_STOCK = "restricted_stock"


# Standard haircuts by collateral category
COLLATERAL_HAIRCUTS = {
    CollateralCategory.CASH: 0.00,
    CollateralCategory.GOVERNMENT_BONDS: 0.02,
    CollateralCategory.INVESTMENT_GRADE: 0.05,
    CollateralCategory.HIGH_YIELD: 0.15,
    CollateralCategory.LARGE_CAP_EQUITY: 0.25,
    CollateralCategory.MID_CAP_EQUITY: 0.35,
    CollateralCategory.SMALL_CAP_EQUITY: 0.50,
    CollateralCategory.ETF: 0.20,
    CollateralCategory.MUTUAL_FUND: 0.25,
    CollateralCategory.RESTRICTED_STOCK: 0.50,
}


@dataclass
class CollateralPosition:
    """Individual collateral position."""
    security_id: str
    security_name: str
    category: CollateralCategory
    quantity: float
    market_value: float
    haircut: Optional[float] = None  # Override default haircut
    currency: Currency = Currency.USD


@dataclass
class MarginLoanTerms:
    """Terms specific to margin loans."""
    loan_type: MarginLoanType = MarginLoanType.SECURITIES_BACKED
    
    # Loan terms
    loan_amount: float = 0.0
    interest_rate_index: FloatingRateIndex = FloatingRateIndex.SOFR
    interest_spread: float = 0.0  # Spread in bps
    
    # Collateral
    collateral_positions: List[CollateralPosition] = field(default_factory=list)
    total_collateral_value: float = 0.0
    
    # Margin requirements
    initial_margin_pct: float = 0.50      # Initial margin requirement
    maintenance_margin_pct: float = 0.35   # Maintenance margin requirement
    
    # Operational
    margin_call_frequency: str = "daily"
    cure_period_days: int = 3
    rehypothecation_allowed: bool = True
    
    # Current state
    current_ltv: float = 0.0              # Current loan-to-value ratio
    margin_excess: float = 0.0            # Excess margin (positive) or deficit


class MarginLoan(BaseProduct):
    """
    Margin Loan (Securities-Based Lending).
    
    A collateralized loan where the borrower pledges securities. The lender
    has exposure to:
    - Credit risk of borrower
    - Market risk of collateral
    - Gap risk (collateral falls faster than can be liquidated)
    
    CCR Considerations:
    - Collateral value fluctuations create exposure
    - Haircuts provide buffer against gap risk
    - Daily margining reduces but doesn't eliminate exposure
    - Wrong-way risk if borrower correlated with collateral
    
    Example:
        loan = MarginLoan(
            trade_id="ML-001",
            trade_date=date.today(),
            effective_date=date.today(),
            maturity_date=date(2025, 12, 31),
            notional=10_000_000,  # Loan amount
            currency=Currency.USD,
            counterparty_id="CLIENT-001",
            terms=MarginLoanTerms(
                loan_type=MarginLoanType.PORTFOLIO_MARGIN,
                loan_amount=10_000_000,
                interest_spread=150,  # SOFR + 150 bps
                initial_margin_pct=0.50
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
        terms: Optional[MarginLoanTerms] = None,
        is_lender: bool = True,
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.MARGIN_LOAN,
            asset_class=AssetClass.SFT,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.terms = terms or MarginLoanTerms(loan_amount=notional)
        self.is_lender = is_lender
        self.day_count = day_count
    
    def get_collateral_value(self, apply_haircuts: bool = True) -> float:
        """
        Calculate total collateral value.
        
        Args:
            apply_haircuts: Whether to apply haircuts
            
        Returns:
            Collateral value (after haircuts if specified)
        """
        if not self.terms.collateral_positions:
            return self.terms.total_collateral_value * (1 - 0.25)  # Default 25% haircut
        
        total = 0.0
        for pos in self.terms.collateral_positions:
            haircut = pos.haircut if pos.haircut is not None else COLLATERAL_HAIRCUTS.get(pos.category, 0.25)
            if apply_haircuts:
                total += pos.market_value * (1 - haircut)
            else:
                total += pos.market_value
        
        return total
    
    def get_ltv(self) -> float:
        """Calculate current loan-to-value ratio."""
        collateral = self.get_collateral_value(apply_haircuts=False)
        if collateral <= 0:
            return float('inf')
        return self.terms.loan_amount / collateral
    
    def get_margin_excess(self) -> float:
        """Calculate margin excess (positive) or deficit (negative)."""
        collateral_after_haircut = self.get_collateral_value(apply_haircuts=True)
        required_collateral = self.terms.loan_amount / (1 - self.terms.maintenance_margin_pct)
        return collateral_after_haircut - required_collateral
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the margin loan from lender's perspective."""
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        remaining = self.get_remaining_maturity(valuation_date)
        elapsed = year_fraction(self.effective_date, valuation_date, self.day_count)
        
        # Interest accrued
        rate = getattr(market_data, 'sofr_rate', 0.05) + self.terms.interest_spread / 10000
        interest_accrued = self.terms.loan_amount * rate * elapsed
        
        # Collateral value
        collateral = self.get_collateral_value(apply_haircuts=True)
        
        # Exposure from lender perspective
        exposure = max(0, self.terms.loan_amount + interest_accrued - collateral)
        
        direction = 1.0 if self.is_lender else -1.0
        npv = direction * (self.terms.loan_amount + interest_accrued)
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "loan_amount": self.terms.loan_amount,
                "interest_accrued": interest_accrued,
                "collateral_value": collateral,
                "exposure": exposure,
                "ltv": self.get_ltv(),
                "margin_excess": self.get_margin_excess()
            },
            greeks={
                "ir_sensitivity": self.terms.loan_amount * remaining * 0.0001
            },
            metadata={
                "product_type": "margin_loan",
                "loan_type": self.terms.loan_type.value,
                "is_lender": self.is_lender
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 1.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure for margin loan."""
        result = self.price(market_data)
        current_exposure = result.components.get("exposure", 0)
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining) if remaining > 0 else time_horizon
        
        # Collateral volatility (assume equity-like for most collateral)
        collateral_vol = 0.25
        
        num_points = 10
        time_grid = list(np.linspace(0, max(0.1, horizon), num_points))
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            # Gap risk increases with time
            vol_factor = collateral_vol * np.sqrt(t) if t > 0 else 0
            
            # Expected exposure considering collateral decline
            base_ee = current_exposure + self.terms.loan_amount * vol_factor * 0.3
            ee_profile.append(max(0, base_ee))
            
            # PFE
            z_score = 1.645 if confidence_level == 0.95 else 2.326
            pfe = base_ee + self.terms.loan_amount * vol_factor * z_score * 0.5
            pfe_profile.append(max(0, pfe))
        
        effective_ee = list(np.maximum.accumulate(ee_profile))
        
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=effective_ee,
            peak_exposure=max(pfe_profile) if pfe_profile else 0,
            epe=np.mean(ee_profile) if ee_profile else 0,
            effective_epe=np.mean(effective_ee) if effective_ee else 0,
            cva=0.0
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """Calculate SA-CCR for margin loan (SFT treatment)."""
        result = self.price(market_data)
        
        # For SFT, exposure = max(0, loan - collateral_after_haircut)
        rc = result.components.get("exposure", 0)
        
        # SFT has simplified treatment - no PFE add-on if properly margined
        pfe_addon = 0.0
        
        ead = max(0, rc)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.SFT,
            metadata={
                "loan_amount": self.terms.loan_amount,
                "collateral_value": self.get_collateral_value(apply_haircuts=True),
                "ltv": self.get_ltv()
            }
        )


__all__ = [
    "MarginLoan",
    "MarginLoanTerms",
    "MarginLoanType",
    "CollateralCategory",
    "CollateralPosition",
    "COLLATERAL_HAIRCUTS",
]
