"""
QLRisk - Stock Loan v2.3.1
=========================================

Stock Loan product implementation for Securities Financing Transactions.

A Stock Loan is a bilateral agreement where the lender transfers ownership
of stock to the borrower, who provides collateral. The borrower pays a fee
(based on the general collateral or special rate) and returns equivalent
securities at maturity.

Key Features:
- Ownership transfer of shares
- Collateral posted (cash or securities)
- Rebate or fee paid to lender
- Dividend and corporate action handling
- Used for short selling, fails coverage, and market making

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass
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


class StockLoanType(Enum):
    """Type of stock loan arrangement."""
    GENERAL_COLLATERAL = "gc"          # Easy to borrow
    SPECIAL = "special"                 # Hard to borrow, higher fee
    WARM = "warm"                       # Moderately hard to borrow
    HOT = "hot"                         # Very hard to borrow


class LoanCollateralType(Enum):
    """Type of collateral for stock loan."""
    CASH = "cash"
    TREASURY = "treasury"
    AGENCY = "agency"
    CORPORATE_BOND = "corporate"
    EQUITY = "equity"
    LETTER_OF_CREDIT = "loc"


class DividendTreatment(Enum):
    """How dividends are handled in the loan."""
    MANUFACTURED = "manufactured"      # Borrower pays manufactured dividend
    WITHHELD = "withheld"              # Dividend withheld, paid at return
    PASS_THROUGH = "pass_through"      # Immediate pass-through


@dataclass
class StockLoanTerms:
    """Terms specific to stock loan transactions."""
    stock_ticker: str = ""
    stock_name: str = ""
    cusip: str = ""
    isin: str = ""
    quantity: int = 0
    loan_value: float = 0.0           # Market value of loaned stock
    loan_type: StockLoanType = StockLoanType.GENERAL_COLLATERAL
    collateral_type: LoanCollateralType = LoanCollateralType.CASH
    collateral_value: float = 0.0
    collateral_margin: float = 1.02   # 102% standard
    rebate_rate: float = 0.0          # Rate paid on cash collateral (can be negative)
    lending_fee: float = 0.0          # Annual fee for non-cash collateral
    haircut: float = 0.0              # Collateral haircut
    dividend_treatment: DividendTreatment = DividendTreatment.MANUFACTURED
    is_open_term: bool = True         # True if open-ended (can be recalled)
    minimum_term_days: int = 0        # Minimum hold period
    recall_notice_days: int = 3       # Notice period for recall
    stock_volatility: float = 0.25    # Annualized volatility
    dividend_yield: float = 0.0       # Expected dividend yield


class StockLoan(BaseProduct):
    """
    Stock Loan Transaction.
    
    A securities financing transaction where securities are lent from the
    lender to the borrower. The borrower posts collateral and pays a fee.
    
    Economics:
    - Lender: Receives fee income, maintains economic exposure, bears counterparty risk
    - Borrower: Gets securities for short selling/fails coverage, pays fee
    
    Cash Collateral:
    - Borrower posts cash (typically 102% of stock value)
    - Lender reinvests cash, pays rebate to borrower
    - Rebate = Investment return - Lending fee
    
    Non-Cash Collateral:
    - Borrower posts securities with appropriate haircut
    - Borrower pays lending fee directly
    
    CCR Considerations:
    - Exposure from gap risk if stock price moves faster than margin calls
    - SA-CCR: Treated as margin lending with securities haircuts
    - Wrong-way risk if collateral is correlated with borrowed stock
    
    Example:
        loan = StockLoan(
            trade_id="SL-001",
            trade_date=date.today(),
            effective_date=date.today(),
            maturity_date=date(2025, 12, 31),
            notional=1_000_000,
            currency=Currency.USD,
            counterparty_id="HEDGE_FUND_001",
            terms=StockLoanTerms(
                stock_ticker="AAPL",
                quantity=5000,
                loan_value=1_000_000,
                loan_type=StockLoanType.GENERAL_COLLATERAL,
                collateral_type=LoanCollateralType.CASH,
                collateral_margin=1.02,
                rebate_rate=0.045  # 4.5% rebate on cash
            ),
            is_lender=True
        )
    """
    
    # Regulatory haircuts by collateral type
    REGULATORY_HAIRCUTS = {
        LoanCollateralType.CASH: 0.00,
        LoanCollateralType.TREASURY: 0.01,
        LoanCollateralType.AGENCY: 0.02,
        LoanCollateralType.CORPORATE_BOND: 0.08,
        LoanCollateralType.EQUITY: 0.15,
        LoanCollateralType.LETTER_OF_CREDIT: 0.00,
    }
    
    # Typical lending fees by loan type (annual)
    TYPICAL_FEES = {
        StockLoanType.GENERAL_COLLATERAL: 0.0025,  # 25 bps
        StockLoanType.WARM: 0.01,                   # 100 bps
        StockLoanType.SPECIAL: 0.05,                # 500 bps
        StockLoanType.HOT: 0.15,                    # 1500 bps
    }
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,
        currency: Currency,
        counterparty_id: str,
        terms: Optional[StockLoanTerms] = None,
        is_lender: bool = True,  # True if we are lending the stock
        day_count: DayCountConvention = DayCountConvention.ACT_360,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.STOCK_LOAN,
            asset_class=AssetClass.EQUITY,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.terms = terms or StockLoanTerms(loan_value=notional)
        self.is_lender = is_lender
        self.day_count = day_count
        
        # Initialize collateral value if not set
        if self.terms.collateral_value == 0:
            self.terms.collateral_value = self.terms.loan_value * self.terms.collateral_margin
        
        # Set default haircut
        if self.terms.haircut == 0:
            self.terms.haircut = self.REGULATORY_HAIRCUTS.get(
                self.terms.collateral_type, 0.05
            )
        
        # Set default fee/rebate based on loan type
        if self.terms.lending_fee == 0 and self.terms.rebate_rate == 0:
            base_fee = self.TYPICAL_FEES.get(self.terms.loan_type, 0.0025)
            if self.terms.collateral_type == LoanCollateralType.CASH:
                # Cash collateral: rebate = reinvestment rate - fee
                self.terms.rebate_rate = 0.05 - base_fee  # Assume 5% reinvestment
            else:
                self.terms.lending_fee = base_fee
    
    def get_current_stock_value(self, market_data: MarketData) -> float:
        """Get current market value of loaned stock."""
        if self.terms.stock_ticker:
            price = market_data.equity_prices.get(
                self.terms.stock_ticker,
                self.terms.loan_value / max(self.terms.quantity, 1)
            )
            return price * self.terms.quantity if self.terms.quantity > 0 else self.terms.loan_value
        return self.terms.loan_value
    
    def get_adjusted_collateral(self) -> float:
        """Get collateral value adjusted for haircut."""
        return self.terms.collateral_value * (1 - self.terms.haircut)
    
    def calculate_margin_call(
        self,
        stock_value: float,
        collateral_value: float
    ) -> float:
        """Calculate margin call amount if any."""
        required = stock_value * self.terms.collateral_margin
        shortfall = required - collateral_value
        return max(0, shortfall)
    
    def price(self, market_data: MarketData) -> PricingResult:
        """
        Price the Stock Loan transaction.
        
        From lender perspective:
        - Asset: Receive stock back at maturity
        - Liability: Return collateral
        - Income: Lending fee
        
        NPV = (Stock Value - Adjusted Collateral) + PV(Fee Income)
        """
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        remaining = self.get_remaining_maturity(valuation_date)
        elapsed = year_fraction(self.effective_date, valuation_date, self.day_count)
        
        # Current stock value
        current_stock_value = self.get_current_stock_value(market_data)
        
        # Collateral (assume constant for simplicity, unless equity collateral)
        if self.terms.collateral_type == LoanCollateralType.EQUITY:
            # Assume equity collateral moves with market
            coll_return = getattr(market_data, 'market_return', 0.0)
            current_collateral = self.terms.collateral_value * (1 + coll_return)
        else:
            current_collateral = self.terms.collateral_value
        
        adjusted_collateral = current_collateral * (1 - self.terms.haircut)
        
        # Fee calculation
        if self.terms.collateral_type == LoanCollateralType.CASH:
            # Rebate is paid to borrower
            net_fee_income = (0.05 - self.terms.rebate_rate) * current_collateral * elapsed
            future_fee = (0.05 - self.terms.rebate_rate) * current_collateral * remaining
        else:
            net_fee_income = self.terms.lending_fee * current_stock_value * elapsed
            future_fee = self.terms.lending_fee * current_stock_value * remaining
        
        # Discount future fee
        discount_curve = market_data.discount_curve
        df = math.exp(-curve_value(discount_curve, remaining, 0.05) * remaining)
        
        # Net exposure
        exposure = max(0, current_stock_value - adjusted_collateral)
        
        # NPV from lender perspective
        if self.is_lender:
            npv = exposure + net_fee_income + future_fee * df
        else:
            npv = -exposure - net_fee_income - future_fee * df
        
        # Margin call check
        margin_call = self.calculate_margin_call(current_stock_value, current_collateral)
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "stock_value": current_stock_value,
                "collateral_value": current_collateral,
                "adjusted_collateral": adjusted_collateral,
                "net_exposure": exposure,
                "accrued_fee": net_fee_income,
                "future_fee_pv": future_fee * df,
                "margin_call": margin_call,
                "remaining_maturity": remaining
            },
            greeks={
                "stock_delta": 1.0 if self.is_lender else -1.0,
                "collateral_delta": -(1 - self.terms.haircut) if self.is_lender else (1 - self.terms.haircut),
                "fee_dv01": current_stock_value * remaining * 0.0001
            },
            metadata={
                "product_type": "stock_loan",
                "loan_type": self.terms.loan_type.value,
                "collateral_type": self.terms.collateral_type.value,
                "is_lender": self.is_lender,
                "stock_ticker": self.terms.stock_ticker
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
        Calculate CCR exposure profile for Stock Loan.
        
        Key risk: Gap risk if stock price moves faster than margin calls.
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
        num_steps = max(12, int(horizon * 52))  # Weekly steps
        time_grid = list(np.linspace(0, horizon, num_steps))
        
        current_stock = result.components.get("stock_value", self.notional)
        current_coll = result.components.get("collateral_value", self.terms.collateral_value)
        
        stock_vol = self.terms.stock_volatility
        coll_vol = 0.0 if self.terms.collateral_type == LoanCollateralType.CASH else 0.10
        correlation = 0.3 if self.terms.collateral_type == LoanCollateralType.EQUITY else 0.0
        
        dt = horizon / num_steps
        
        # Simulate paths with correlation
        z1 = np.random.standard_normal((num_scenarios, num_steps))
        z2 = correlation * z1 + np.sqrt(1 - correlation**2) * np.random.standard_normal((num_scenarios, num_steps))
        
        stock_paths = np.zeros((num_scenarios, num_steps + 1))
        coll_paths = np.zeros((num_scenarios, num_steps + 1))
        stock_paths[:, 0] = current_stock
        coll_paths[:, 0] = current_coll
        
        for i in range(num_steps):
            stock_paths[:, i+1] = stock_paths[:, i] * np.exp(-0.5 * stock_vol**2 * dt + stock_vol * np.sqrt(dt) * z1[:, i])
            if coll_vol > 0:
                coll_paths[:, i+1] = coll_paths[:, i] * np.exp(-0.5 * coll_vol**2 * dt + coll_vol * np.sqrt(dt) * z2[:, i])
            else:
                coll_paths[:, i+1] = coll_paths[:, i]
        
        # Calculate exposures
        ee_profile = []
        pfe_profile = []
        
        for i in range(len(time_grid)):
            adj_coll = coll_paths[:, i] * (1 - self.terms.haircut)
            exposures = np.maximum(0, stock_paths[:, i] - adj_coll)
            
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
            peak_exposure=max(pfe_profile) if pfe_profile else 0,
            epe=np.mean(ee_profile) if ee_profile else 0,
            effective_epe=np.mean(effective_ee) if effective_ee else 0,
            cva=0.0
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """
        Calculate SA-CCR EAD for Stock Loan.
        
        For SFT (Margin Lending):
        EAD = max(0, E * (1 + H_s) - C * (1 - H_c) + H_fx)
        
        Where:
        - E = Securities (stock) value
        - H_s = Securities (volatility) haircut
        - C = Collateral value  
        - H_c = Collateral haircut
        - H_fx = FX haircut if different currencies
        """
        result = self.price(market_data)
        
        stock_value = result.components.get("stock_value", self.notional)
        coll_value = result.components.get("collateral_value", self.terms.collateral_value)
        
        # Standard supervisory haircut for equity
        stock_haircut = 0.15  # 15% for equity
        coll_haircut = self.terms.haircut
        
        # Adjusted values
        adjusted_stock = stock_value * (1 + stock_haircut)
        adjusted_coll = coll_value * (1 - coll_haircut)
        
        # EAD
        ead = max(0, adjusted_stock - adjusted_coll)
        
        return SACCRExposure(
            replacement_cost=max(0, stock_value - adjusted_coll),
            pfe_add_on=stock_value * stock_haircut,
            ead=ead,
            asset_class=AssetClass.EQUITY,
            metadata={
                "stock_value": stock_value,
                "collateral_value": coll_value,
                "stock_haircut": stock_haircut,
                "collateral_haircut": coll_haircut,
                "adjusted_stock": adjusted_stock,
                "adjusted_collateral": adjusted_coll,
                "loan_type": self.terms.loan_type.value
            }
        )
    
    def __repr__(self) -> str:
        return (
            f"StockLoan(trade_id='{self.trade_id}', "
            f"stock='{self.terms.stock_ticker}', "
            f"qty={self.terms.quantity}, "
            f"type={self.terms.loan_type.value}, "
            f"lender={self.is_lender})"
        )


__all__ = [
    "StockLoan",
    "StockLoanType",
    "StockLoanTerms",
    "LoanCollateralType",
    "DividendTreatment",
]
