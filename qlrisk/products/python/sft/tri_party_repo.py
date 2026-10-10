"""
QLRisk - Tri-Party Repo v2.2.0
=============================================

Tri-Party Repurchase Agreement implementation with full CCR analytics.

A Tri-Party Repo is a repurchase agreement where a third-party agent (typically
a clearing bank) manages collateral allocation, valuation, and settlement between
the cash lender and securities borrower.

Key Features:
- Third-party collateral management
- Daily collateral valuation and substitution
- Standardized eligibility and haircut schedules
- Operational efficiency vs bilateral repo

Tri-Party Agents:
- BNY Mellon (US)
- JP Morgan (US)
- Euroclear (Europe)
- Clearstream (Europe)

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from datetime import date
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import numpy as np

from ...base import (
    BaseProduct, ProductType, AssetClass, Currency,
    DayCountConvention, FloatingRateIndex,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class TriPartyAgent(Enum):
    """Tri-party agent/custodian."""
    BNY_MELLON = "bny_mellon"
    JP_MORGAN = "jp_morgan"
    EUROCLEAR = "euroclear"
    CLEARSTREAM = "clearstream"
    STATE_STREET = "state_street"
    NORTHERN_TRUST = "northern_trust"


class CollateralSchedule(Enum):
    """Standardized collateral schedules."""
    GOVERNMENT_ONLY = "government_only"
    GOVERNMENT_PLUS = "government_plus"
    INVESTMENT_GRADE = "investment_grade"
    BROAD_MARKET = "broad_market"
    CUSTOM = "custom"


# Weighted average haircuts by schedule
SCHEDULE_HAIRCUTS = {
    CollateralSchedule.GOVERNMENT_ONLY: 0.02,
    CollateralSchedule.GOVERNMENT_PLUS: 0.03,
    CollateralSchedule.INVESTMENT_GRADE: 0.05,
    CollateralSchedule.BROAD_MARKET: 0.08,
    CollateralSchedule.CUSTOM: 0.05,
}


@dataclass
class TriPartyRepoTerms:
    """Terms specific to tri-party repos."""
    # Agent
    agent: TriPartyAgent = TriPartyAgent.BNY_MELLON
    
    # Repo terms
    cash_amount: float = 0.0
    repo_rate: float = 0.0             # Fixed rate (annual)
    is_floating_rate: bool = False
    floating_index: FloatingRateIndex = FloatingRateIndex.SOFR
    floating_spread: float = 0.0       # Spread in bps
    
    # Collateral
    collateral_schedule: CollateralSchedule = CollateralSchedule.GOVERNMENT_ONLY
    collateral_value: float = 0.0
    collateral_securities: List[str] = field(default_factory=list)
    haircut: Optional[float] = None    # Override schedule haircut
    
    # Operational
    is_open: bool = False              # Open repo (no fixed maturity)
    auto_roll: bool = True
    substitution_allowed: bool = True
    
    # GC vs Special
    is_gc: bool = True                 # General Collateral
    special_security: str = ""         # If special repo


class TriPartyRepo(BaseProduct):
    """
    Tri-Party Repurchase Agreement.
    
    A repo where a tri-party agent manages collateral between cash lender
    (reverse repo party) and securities borrower (repo party).
    
    Cash Lender (Reverse Repo):
    - Provides cash
    - Receives interest
    - Has claim on collateral if counterparty defaults
    
    Securities Borrower (Repo):
    - Receives cash
    - Pays interest
    - Pledges securities as collateral
    
    Example:
        repo = TriPartyRepo(
            trade_id="TPR-001",
            trade_date=date.today(),
            effective_date=date.today(),
            maturity_date=date(2025, 1, 15),  # Or None for open
            notional=500_000_000,
            currency=Currency.USD,
            counterparty_id="DEALER-001",
            terms=TriPartyRepoTerms(
                agent=TriPartyAgent.BNY_MELLON,
                cash_amount=500_000_000,
                repo_rate=0.052,  # 5.2%
                collateral_schedule=CollateralSchedule.GOVERNMENT_ONLY
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
        terms: Optional[TriPartyRepoTerms] = None,
        is_cash_lender: bool = True,
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.TRI_PARTY_REPO,
            asset_class=AssetClass.SFT,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.terms = terms or TriPartyRepoTerms(cash_amount=notional)
        self.is_cash_lender = is_cash_lender
        self.day_count = day_count
    
    def get_repo_rate(self, market_data: MarketData) -> float:
        """Get the effective repo rate."""
        if self.terms.is_floating_rate:
            base_rate = getattr(market_data, 'sofr_rate', 0.05)
            return base_rate + self.terms.floating_spread / 10000
        return self.terms.repo_rate
    
    def get_haircut(self) -> float:
        """Get the applicable haircut."""
        if self.terms.haircut is not None:
            return self.terms.haircut
        return SCHEDULE_HAIRCUTS.get(self.terms.collateral_schedule, 0.05)
    
    def get_required_collateral(self) -> float:
        """Calculate required collateral value."""
        haircut = self.get_haircut()
        return self.terms.cash_amount / (1 - haircut)
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price the tri-party repo."""
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        remaining = self.get_remaining_maturity(valuation_date)
        elapsed = year_fraction(self.effective_date, valuation_date, self.day_count)
        
        # Interest calculation
        rate = self.get_repo_rate(market_data)
        interest_accrued = self.terms.cash_amount * rate * elapsed
        
        # Value from cash lender perspective
        collateral = self.terms.collateral_value or self.get_required_collateral()
        haircut = self.get_haircut()
        collateral_after_haircut = collateral * (1 - haircut)
        
        # Exposure
        exposure = max(0, self.terms.cash_amount + interest_accrued - collateral_after_haircut)
        
        direction = 1.0 if self.is_cash_lender else -1.0
        npv = direction * (self.terms.cash_amount + interest_accrued)
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "cash_amount": self.terms.cash_amount,
                "interest_accrued": interest_accrued,
                "repo_rate": rate,
                "collateral_value": collateral,
                "haircut": haircut,
                "exposure": exposure,
                "remaining_maturity": remaining
            },
            greeks={
                "rate_sensitivity": self.terms.cash_amount * remaining * 0.0001
            },
            metadata={
                "product_type": "tri_party_repo",
                "agent": self.terms.agent.value,
                "schedule": self.terms.collateral_schedule.value,
                "is_gc": self.terms.is_gc
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 1.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure for tri-party repo."""
        result = self.price(market_data)
        current_exposure = result.components.get("exposure", 0)
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining) if remaining > 0 else time_horizon
        
        # Low volatility due to daily margining
        vol = 0.02
        
        num_points = 10
        time_grid = list(np.linspace(0, max(0.1, horizon), num_points))
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            vol_factor = vol * np.sqrt(t) if t > 0 else 0
            base_ee = current_exposure + self.terms.cash_amount * vol_factor * 0.05
            ee_profile.append(max(0, base_ee))
            
            z_score = 1.645 if confidence_level == 0.95 else 2.326
            pfe = base_ee + self.terms.cash_amount * vol_factor * z_score * 0.1
            pfe_profile.append(max(0, pfe))
        
        effective_ee = list(np.maximum.accumulate(ee_profile))
        
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=effective_ee,
            peak_exposure=max(pfe_profile) if pfe_profile else 0,
            epe=np.mean(ee_profile),
            effective_epe=np.mean(effective_ee),
            cva=0.0
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """Calculate SA-CCR for tri-party repo."""
        result = self.price(market_data)
        rc = result.components.get("exposure", 0)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=0.0,
            ead=max(0, rc),
            asset_class=AssetClass.SFT,
            details={
                "agent": self.terms.agent.value,
                "schedule": self.terms.collateral_schedule.value,
                "haircut": self.get_haircut()
            }
        )


__all__ = [
    "TriPartyRepo",
    "TriPartyRepoTerms",
    "TriPartyAgent",
    "CollateralSchedule",
    "SCHEDULE_HAIRCUTS",
]
