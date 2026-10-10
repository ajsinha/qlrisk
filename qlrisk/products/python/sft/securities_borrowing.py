"""
QLRisk - Securities Borrowing v1.3.0
===================================================

Securities Borrowing product implementation for Securities Financing Transactions.

In a securities borrowing transaction:
- Borrower receives securities from lender
- Borrower posts cash or other collateral to lender
- Borrower pays a fee (rebate rate)
- At maturity, securities are returned and collateral is returned

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


class CollateralType(Enum):
    """Type of collateral posted."""
    CASH = "cash"
    GOVERNMENT_BONDS = "government_bonds"
    CORPORATE_BONDS = "corporate_bonds"
    EQUITIES = "equities"
    MONEY_MARKET = "money_market"
    LETTER_OF_CREDIT = "letter_of_credit"


class SecuritiesType(Enum):
    """Type of securities borrowed."""
    EQUITY = "equity"
    GOVERNMENT_BOND = "government_bond"
    CORPORATE_BOND = "corporate_bond"
    ETF = "etf"
    CONVERTIBLE = "convertible"


@dataclass
class BorrowedSecurity:
    """Details of borrowed security."""
    security_id: str
    security_type: SecuritiesType = SecuritiesType.EQUITY
    ticker: str = ""
    isin: str = ""
    quantity: float = 0.0
    market_value: float = 0.0
    haircut: float = 0.0
    volatility: float = 0.20
    dividend_yield: float = 0.0
    is_hard_to_borrow: bool = False
    special_rate: Optional[float] = None  # If hard to borrow


class SecuritiesBorrowing(BaseProduct):
    """
    Securities Borrowing Transaction.
    
    A transaction where one party (borrower) borrows securities from another
    party (lender), posting collateral and paying a borrowing fee.
    
    Key Features:
    - Borrower receives securities, posts collateral
    - Fee calculated as rebate rate on collateral value
    - Collateral marked-to-market daily
    - Margin calls if collateral falls below requirement
    
    Use Cases:
    - Short selling coverage
    - Settlement fails coverage
    - Collateral transformation
    - Dividend arbitrage
    
    CCR Characteristics:
    - Exposure = max(0, Securities Value - Collateral Value × (1 - Haircut))
    - Risk from securities price movements and collateral value changes
    """
    
    # Standard haircuts by collateral type
    STANDARD_HAIRCUTS = {
        CollateralType.CASH: 0.0,
        CollateralType.GOVERNMENT_BONDS: 0.02,
        CollateralType.CORPORATE_BONDS: 0.08,
        CollateralType.EQUITIES: 0.15,
        CollateralType.MONEY_MARKET: 0.01,
        CollateralType.LETTER_OF_CREDIT: 0.0,
    }
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,  # Market value of borrowed securities
        currency: Currency,
        counterparty_id: str,
        # Securities Borrowing specific
        borrowed_securities: Optional[List[BorrowedSecurity]] = None,
        collateral_type: CollateralType = CollateralType.CASH,
        collateral_value: float = 0.0,
        collateral_haircut: Optional[float] = None,
        rebate_rate: float = -0.0025,  # Negative = borrower pays
        margin_ratio: float = 1.02,    # 102% initial margin
        minimum_margin: float = 1.00,  # 100% maintenance margin
        is_term: bool = False,         # True if fixed term, False if open
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.SECURITIES_LENDING,  # Reuse for borrowing
            asset_class=AssetClass.EQUITY,  # Default, may change based on security
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.borrowed_securities = borrowed_securities or [
            BorrowedSecurity(
                security_id="DEFAULT",
                market_value=notional
            )
        ]
        self.collateral_type = collateral_type
        self.collateral_value = collateral_value or (notional * margin_ratio)
        self.collateral_haircut = collateral_haircut or self.STANDARD_HAIRCUTS.get(collateral_type, 0.05)
        self.rebate_rate = rebate_rate
        self.margin_ratio = margin_ratio
        self.minimum_margin = minimum_margin
        self.is_term = is_term
        self.day_count = day_count
    
    def _calculate_net_exposure(
        self,
        securities_value: float,
        collateral_value: float
    ) -> float:
        """Calculate net exposure after collateral."""
        adjusted_collateral = collateral_value * (1 - self.collateral_haircut)
        return max(0, securities_value - adjusted_collateral)
    
    def _calculate_margin_call(
        self,
        securities_value: float,
        collateral_value: float
    ) -> float:
        """Calculate margin call amount if any."""
        required_collateral = securities_value * self.margin_ratio
        shortfall = required_collateral - collateral_value
        return max(0, shortfall)
    
    def price(self, market_data: MarketData) -> PricingResult:
        """
        Price the Securities Borrowing transaction.
        
        Value = Securities Value - Adjusted Collateral Value - Accrued Fee
        """
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        remaining = self.get_remaining_maturity(valuation_date)
        elapsed = year_fraction(self.effective_date, valuation_date, self.day_count)
        
        # Calculate current securities value
        current_securities_value = 0.0
        for security in self.borrowed_securities:
            price = market_data.equity_prices.get(
                security.ticker or security.security_id,
                security.market_value / max(security.quantity, 1)
            )
            current_securities_value += price * security.quantity if security.quantity > 0 else security.market_value
        
        # Update collateral value (assume collateral tracks market)
        if self.collateral_type == CollateralType.CASH:
            current_collateral = self.collateral_value
        else:
            # Apply some volatility to non-cash collateral
            collateral_return = np.random.normal(0, 0.01)  # Simplified
            current_collateral = self.collateral_value * (1 + collateral_return)
        
        # Calculate accrued fee
        accrued_fee = abs(self.rebate_rate) * self.collateral_value * elapsed
        
        # Calculate expected future fee
        future_fee = abs(self.rebate_rate) * self.collateral_value * remaining
        
        # Net exposure
        net_exposure = self._calculate_net_exposure(current_securities_value, current_collateral)
        
        # NPV from borrower perspective (liability)
        npv = -(net_exposure + accrued_fee)
        
        # Get discount factor
        discount_curve = market_data.discount_curve
        df = math.exp(-curve_value(discount_curve, remaining, 0.05) * remaining)
        
        # Add PV of future fees
        npv -= future_fee * df
        
        # Margin call calculation
        margin_call = self._calculate_margin_call(current_securities_value, current_collateral)
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "securities_value": current_securities_value,
                "collateral_value": current_collateral,
                "adjusted_collateral": current_collateral * (1 - self.collateral_haircut),
                "net_exposure": net_exposure,
                "accrued_fee": accrued_fee,
                "margin_call": margin_call,
                "remaining_maturity": remaining
            },
            greeks={
                "securities_delta": 1.0,
                "collateral_delta": -(1 - self.collateral_haircut),
                "rate_sensitivity": self.collateral_value * remaining
            },
            metadata={
                "product_type": "securities_borrowing",
                "collateral_type": self.collateral_type.value,
                "is_term": self.is_term,
                "num_securities": len(self.borrowed_securities),
                "haircut": self.collateral_haircut
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 1.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """
        Calculate CCR exposure profile.
        
        For SFT, exposure is driven by:
        - Securities price movements
        - Collateral value changes
        - Correlation between the two
        """
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
        num_steps = max(4, int(horizon * 12))  # Monthly steps
        time_grid = list(np.linspace(0, horizon, num_steps))
        
        # Simulation parameters
        securities_vol = np.mean([s.volatility for s in self.borrowed_securities])
        collateral_vol = 0.01 if self.collateral_type == CollateralType.CASH else 0.05
        correlation = 0.5  # Securities-collateral correlation
        
        current_sec_value = result.components.get("securities_value", self.notional)
        current_coll_value = result.components.get("collateral_value", self.collateral_value)
        
        dt = horizon / num_steps
        
        # Correlated random numbers
        z1 = np.random.standard_normal((num_scenarios, num_steps))
        z2 = correlation * z1 + np.sqrt(1 - correlation**2) * np.random.standard_normal((num_scenarios, num_steps))
        
        # Simulate paths
        sec_paths = np.zeros((num_scenarios, num_steps + 1))
        coll_paths = np.zeros((num_scenarios, num_steps + 1))
        sec_paths[:, 0] = current_sec_value
        coll_paths[:, 0] = current_coll_value
        
        for i in range(num_steps):
            sec_paths[:, i+1] = sec_paths[:, i] * np.exp(-0.5 * securities_vol**2 * dt + securities_vol * np.sqrt(dt) * z1[:, i])
            if self.collateral_type != CollateralType.CASH:
                coll_paths[:, i+1] = coll_paths[:, i] * np.exp(-0.5 * collateral_vol**2 * dt + collateral_vol * np.sqrt(dt) * z2[:, i])
            else:
                coll_paths[:, i+1] = coll_paths[:, i]  # Cash doesn't change
        
        # Calculate exposures
        ee_profile = []
        pfe_profile = []
        
        for i, t in enumerate(time_grid):
            exposures = np.maximum(0, sec_paths[:, i] - coll_paths[:, i] * (1 - self.collateral_haircut))
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
        """
        Calculate SA-CCR EAD for Securities Borrowing.
        
        For SFT, SA-CCR uses simplified approach:
        EAD = max(0, E - C × (1 - H_c) + H_s × E)
        
        Where:
        - E = Securities value
        - C = Collateral value
        - H_c = Collateral haircut
        - H_s = Securities haircut
        """
        result = self.price(market_data)
        
        sec_value = result.components.get("securities_value", self.notional)
        coll_value = result.components.get("collateral_value", self.collateral_value)
        
        # Securities haircut based on type
        sec_haircut = 0.15 if self.borrowed_securities[0].security_type == SecuritiesType.EQUITY else 0.05
        
        # Regulatory EAD calculation for SFT
        adjusted_exposure = sec_value * (1 + sec_haircut)
        adjusted_collateral = coll_value * (1 - self.collateral_haircut)
        
        ead = max(0, adjusted_exposure - adjusted_collateral)
        
        return SACCRExposure(
            replacement_cost=max(0, sec_value - adjusted_collateral),
            pfe_add_on=sec_value * sec_haircut,
            ead=ead,
            asset_class=AssetClass.EQUITY,
            details={
                "securities_value": sec_value,
                "collateral_value": coll_value,
                "securities_haircut": sec_haircut,
                "collateral_haircut": self.collateral_haircut,
                "adjusted_exposure": adjusted_exposure,
                "adjusted_collateral": adjusted_collateral
            }
        )


__all__ = ["SecuritiesBorrowing", "CollateralType", "SecuritiesType", "BorrowedSecurity"]
