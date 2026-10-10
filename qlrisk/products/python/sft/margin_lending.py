"""
QLRisk - Margin Lending v2.1.0
=============================================

Margin Lending product implementation for Securities Financing Transactions.

In a margin lending transaction:
- Lender provides cash to borrower
- Borrower posts securities as collateral
- Borrower pays interest on the loan
- Collateral marked-to-market with margin calls

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


class LoanPurpose(Enum):
    """Purpose of the margin loan."""
    SECURITIES_PURCHASE = "securities_purchase"
    WORKING_CAPITAL = "working_capital"
    BRIDGE_FINANCING = "bridge_financing"
    PORTFOLIO_LEVERAGE = "portfolio_leverage"


@dataclass 
class CollateralPosition:
    """Individual collateral position."""
    security_id: str
    ticker: str = ""
    quantity: float = 0.0
    market_value: float = 0.0
    haircut: float = 0.25  # 25% default for equities
    concentration_limit: float = 0.30  # Max 30% in single security
    eligibility: bool = True
    volatility: float = 0.25


class MarginLending(BaseProduct):
    """
    Margin Lending Transaction.
    
    A transaction where a lender provides cash financing to a borrower,
    secured by a portfolio of securities as collateral.
    
    Key Features:
    - Cash loan secured by securities collateral
    - Interest charged on loan amount
    - Daily mark-to-market of collateral
    - Margin calls if collateral value falls
    - Concentration limits on collateral
    
    Use Cases:
    - Prime brokerage financing
    - Portfolio leverage
    - Securities purchase financing
    - Working capital for investment funds
    
    CCR Characteristics:
    - Exposure = Loan Amount - Adjusted Collateral Value
    - Risk from collateral price movements
    - Concentration risk from single-name exposure
    """
    
    # Haircuts by security type
    STANDARD_HAIRCUTS = {
        "large_cap_equity": 0.20,
        "mid_cap_equity": 0.30,
        "small_cap_equity": 0.40,
        "etf": 0.15,
        "government_bond": 0.05,
        "corporate_bond_ig": 0.10,
        "corporate_bond_hy": 0.20,
    }
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,  # Loan principal amount
        currency: Currency,
        counterparty_id: str,
        # Margin Lending specific
        collateral_positions: Optional[List[CollateralPosition]] = None,
        loan_rate: float = 0.05,  # Annual interest rate
        reference_rate: str = "SOFR",
        spread: float = 0.02,     # Spread over reference rate
        initial_margin_ratio: float = 1.50,   # 150% initial margin
        maintenance_margin_ratio: float = 1.25,  # 125% maintenance
        margin_call_frequency: str = "daily",
        loan_purpose: LoanPurpose = LoanPurpose.PORTFOLIO_LEVERAGE,
        is_committed: bool = True,  # Committed vs uncommitted facility
        facility_limit: Optional[float] = None,
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.REPO,  # Use REPO type for SFT
            asset_class=AssetClass.EQUITY,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.collateral_positions = collateral_positions or []
        self.loan_rate = loan_rate
        self.reference_rate = reference_rate
        self.spread = spread
        self.initial_margin_ratio = initial_margin_ratio
        self.maintenance_margin_ratio = maintenance_margin_ratio
        self.margin_call_frequency = margin_call_frequency
        self.loan_purpose = loan_purpose
        self.is_committed = is_committed
        self.facility_limit = facility_limit or (notional * 1.5)
        self.day_count = day_count
        
        # If no collateral specified, create default
        if not self.collateral_positions:
            required_collateral = notional * initial_margin_ratio
            self.collateral_positions = [
                CollateralPosition(
                    security_id="DEFAULT_COLLATERAL",
                    market_value=required_collateral
                )
            ]
    
    def _get_total_collateral_value(self, market_data: Optional[MarketData] = None) -> float:
        """Get total collateral value after haircuts."""
        total = 0.0
        for pos in self.collateral_positions:
            if market_data and pos.ticker:
                current_price = market_data.equity_prices.get(pos.ticker, pos.market_value / max(pos.quantity, 1))
                current_value = current_price * pos.quantity if pos.quantity > 0 else pos.market_value
            else:
                current_value = pos.market_value
            
            adjusted_value = current_value * (1 - pos.haircut)
            total += adjusted_value
        return total
    
    def _calculate_margin_ratio(self, collateral_value: float) -> float:
        """Calculate current margin ratio."""
        if self.notional > 0:
            return collateral_value / self.notional
        return float('inf')
    
    def _calculate_margin_call(self, collateral_value: float) -> float:
        """Calculate margin call amount if below maintenance."""
        current_ratio = self._calculate_margin_ratio(collateral_value)
        if current_ratio < self.maintenance_margin_ratio:
            required = self.notional * self.initial_margin_ratio
            shortfall = required - collateral_value
            return max(0, shortfall)
        return 0.0
    
    def price(self, market_data: MarketData) -> PricingResult:
        """
        Price the Margin Lending facility.
        
        From lender perspective:
        Value = Loan Principal + Accrued Interest - Expected Loss
        """
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        remaining = self.get_remaining_maturity(valuation_date)
        elapsed = year_fraction(self.effective_date, valuation_date, self.day_count)
        
        # Get reference rate
        ref_rate = market_data.reference_rates.get(self.reference_rate, 0.05)
        effective_rate = ref_rate + self.spread
        
        # Calculate collateral value
        total_collateral = 0.0
        adjusted_collateral = 0.0
        for pos in self.collateral_positions:
            if pos.ticker:
                current_price = market_data.equity_prices.get(
                    pos.ticker,
                    pos.market_value / max(pos.quantity, 1)
                )
                current_value = current_price * pos.quantity if pos.quantity > 0 else pos.market_value
            else:
                current_value = pos.market_value
            total_collateral += current_value
            adjusted_collateral += current_value * (1 - pos.haircut)
        
        # Accrued interest
        accrued_interest = self.notional * effective_rate * elapsed
        
        # Expected future interest
        future_interest = self.notional * effective_rate * remaining
        
        # Discount factor
        discount_curve = market_data.discount_curve
        df = math.exp(-curve_value(discount_curve, remaining, 0.05) * remaining)
        
        # Net exposure
        net_exposure = max(0, self.notional - adjusted_collateral)
        
        # Margin ratio and call
        margin_ratio = self._calculate_margin_ratio(adjusted_collateral)
        margin_call = self._calculate_margin_call(adjusted_collateral)
        
        # NPV from lender perspective
        npv = self.notional + accrued_interest + future_interest * df
        
        # Adjust for credit risk (simplified)
        expected_loss = net_exposure * 0.01  # 1% expected loss on exposure
        npv -= expected_loss
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "loan_principal": self.notional,
                "accrued_interest": accrued_interest,
                "total_collateral": total_collateral,
                "adjusted_collateral": adjusted_collateral,
                "net_exposure": net_exposure,
                "margin_ratio": margin_ratio,
                "margin_call": margin_call,
                "effective_rate": effective_rate,
                "remaining_maturity": remaining
            },
            greeks={
                "interest_rate_sensitivity": self.notional * remaining * 0.0001,
                "collateral_delta": -(1 - np.mean([p.haircut for p in self.collateral_positions]))
            },
            metadata={
                "product_type": "margin_lending",
                "loan_purpose": self.loan_purpose.value,
                "is_committed": self.is_committed,
                "num_collateral_positions": len(self.collateral_positions),
                "maintenance_margin": self.maintenance_margin_ratio
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 1.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure profile with collateral simulation."""
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
        
        # Collateral volatility (weighted average)
        avg_volatility = np.mean([p.volatility for p in self.collateral_positions])
        avg_haircut = np.mean([p.haircut for p in self.collateral_positions])
        
        current_collateral = result.components.get("total_collateral", self.notional * self.initial_margin_ratio)
        
        dt = horizon / num_steps
        z = np.random.standard_normal((num_scenarios, num_steps))
        
        # Simulate collateral paths
        coll_paths = np.zeros((num_scenarios, num_steps + 1))
        coll_paths[:, 0] = current_collateral
        
        for i in range(num_steps):
            coll_paths[:, i+1] = coll_paths[:, i] * np.exp(-0.5 * avg_volatility**2 * dt + avg_volatility * np.sqrt(dt) * z[:, i])
        
        # Calculate exposures
        ee_profile = []
        pfe_profile = []
        
        for i, t in enumerate(time_grid):
            adjusted_coll = coll_paths[:, i] * (1 - avg_haircut)
            exposures = np.maximum(0, self.notional - adjusted_coll)
            ee_profile.append(float(np.mean(exposures)))
            pfe_profile.append(float(np.percentile(exposures, confidence_level * 100)))
        
        # Effective EE
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
        """Calculate SA-CCR EAD for Margin Lending."""
        result = self.price(market_data)
        
        loan_value = self.notional
        adjusted_coll = result.components.get("adjusted_collateral", 0)
        
        # SFT approach
        avg_haircut = np.mean([p.haircut for p in self.collateral_positions])
        
        ead = max(0, loan_value - adjusted_coll + loan_value * 0.10)  # 10% add-on
        
        return SACCRExposure(
            replacement_cost=max(0, loan_value - adjusted_coll),
            pfe_add_on=loan_value * 0.10,
            ead=ead,
            asset_class=AssetClass.EQUITY,
            details={
                "loan_value": loan_value,
                "adjusted_collateral": adjusted_coll,
                "average_haircut": avg_haircut,
                "margin_ratio": result.components.get("margin_ratio", 0)
            }
        )


__all__ = ["MarginLending", "LoanPurpose", "CollateralPosition"]
