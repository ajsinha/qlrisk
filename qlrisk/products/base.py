"""
QLRisk - Products Base Module
===============================================

Base classes and enumerations for all derivative products supported by the
QLRisk. Provides common interfaces for pricing, risk calculation,
and CCR exposure computation across all asset classes.

Supported Asset Classes:
- Interest Rates (IRS, OIS, FRA, Caps/Floors, Swaptions)
- Foreign Exchange (Forwards, Swaps, Options, NDF)
- Credit (CDS, CDS Index, TRS, CLN)
- Equity (Swaps, Options, Variance Swaps, Dividend Swaps)
- Commodities (Swaps, Options, Forwards)
- Cross-Currency (XCCY Swaps, Basis Swaps)
- Repo/Securities Financing (Repo, Reverse Repo, Securities Lending)

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from abc import ABC, abstractmethod
from bisect import bisect_right
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum, auto
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np


# =============================================================================
# Enumerations
# =============================================================================

class AssetClass(Enum):
    """Primary asset class classification."""
    INTEREST_RATE = "interest_rate"
    FX = "fx"
    CREDIT = "credit"
    EQUITY = "equity"
    COMMODITY = "commodity"
    CROSS_CURRENCY = "cross_currency"
    REPO = "repo"
    FIXED_INCOME = "fixed_income"
    SFT = "securities_financing"
    MONEY_MARKET = "money_market"
    ALTERNATIVES = "alternatives"


class ProductType(Enum):
    """Enumeration of all supported product types."""
    
    # Interest Rate Derivatives
    IRS = "interest_rate_swap"
    OIS = "overnight_index_swap"
    FRA = "forward_rate_agreement"
    CAP = "interest_rate_cap"
    FLOOR = "interest_rate_floor"
    SWAPTION = "swaption"
    BASIS_SWAP = "basis_swap"
    COLLAR = "collar"
    INFLATION_SWAP = "inflation_swap"
    ZERO_COUPON_SWAP = "zc_swap"
    AMORTIZING_SWAP = "amort_swap"
    
    # FX Products
    FX_FORWARD = "fx_forward"
    FX_SWAP = "fx_swap"
    FX_OPTION = "fx_option"
    FX_BARRIER = "fx_barrier_option"
    NDF = "non_deliverable_forward"
    FX_DIGITAL = "fx_digital_option"
    
    # Credit Products
    CDS = "credit_default_swap"
    CDS_INDEX = "cds_index"
    TRS = "total_return_swap"
    CLN = "credit_linked_note"
    FIRST_TO_DEFAULT = "ftd"
    
    # Equity Derivatives
    EQUITY_SWAP = "equity_swap"
    EQUITY_OPTION = "equity_option"
    EQUITY_FORWARD = "equity_forward"
    VARIANCE_SWAP = "variance_swap"
    DIVIDEND_SWAP = "dividend_swap"
    VOLATILITY_SWAP = "vol_swap"
    CFD = "cfd"
    
    # Commodity Products
    COMMODITY_SWAP = "commodity_swap"
    COMMODITY_OPTION = "commodity_option"
    COMMODITY_FORWARD = "commodity_forward"
    COMMODITY_SWAPTION = "commodity_swptn"
    
    # Cross-Currency Products
    XCCY_SWAP = "cross_currency_swap"
    XCCY_BASIS = "cross_currency_basis_swap"
    MTM_XCCY = "mtm_cross_currency_swap"
    MTMXCCY = "mtm_xccy"  # Alias
    
    # Repo Products
    REPO = "repo"
    REVERSE_REPO = "reverse_repo"
    SECURITIES_LENDING = "securities_lending"
    BUY_SELL_BACK = "buy_sell_back"
    
    # Money Market Products
    CD = "certificate_of_deposit"
    BANKERS_ACCEPTANCE = "bankers_acceptance"
    EURODOLLAR = "eurodollar_deposit"
    FED_FUNDS = "federal_funds"
    MMF = "money_market_fund"
    TIME_DEPOSIT = "time_deposit"
    DISCOUNT_NOTE = "discount_note"
    
    # Stocks & ETFs
    COMMON_STOCK = "common_stock"
    ADR = "adr"
    GDR = "gdr"
    PREFERRED_STOCK = "preferred_stock"
    WARRANT = "warrant"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    INDEX_POSITION = "index_position"
    
    # Alternative Investments
    CRYPTO_SPOT = "crypto_spot"
    CRYPTO_FUTURE = "crypto_future"
    CRYPTO_PERPETUAL = "crypto_perpetual"
    REIT = "reit"
    CARBON_CREDIT = "carbon_credit"
    CARBON_FUTURE = "carbon_future"
    PE_INTEREST = "private_equity_interest"
    HF_INTEREST = "hedge_fund_interest"
    
    # Futures
    INDEX_FUTURE = "index_future"
    IR_FUTURE = "interest_rate_future"
    BOND_FUTURE = "bond_future"
    VIX_FUTURE = "vix_future"
    SSF = "single_stock_future"
    COMMODITY_FUTURE = "commodity_future"
    
    # Total Return Swaps
    EQUITY_TRS = "equity_trs"
    BOND_TRS = "bond_trs"
    
    # Securities Financing Transactions (SFT)
    MARGIN_LOAN = "margin_loan"
    COLLATERAL_SWAP = "collateral_swap"
    TRI_PARTY_REPO = "tri_party_repo"
    PRIME_BROKERAGE = "prime_brokerage"
    STOCK_LOAN = "stock_loan"
    
    # Fixed Income - Government
    TREASURY_BILL = "treasury_bill"
    TREASURY_NOTE = "treasury_note"
    TREASURY_BOND = "treasury_bond"
    TIPS = "tips"
    UK_GILT = "uk_gilt"
    GERMAN_BUND = "german_bund"
    JGB = "jgb"
    FRENCH_OAT = "french_oat"
    GOVERNMENT_BOND = "government_bond"
    
    # Fixed Income - Other
    MUNICIPAL_BOND = "municipal_bond"
    AGENCY_BOND = "agency_bond"
    CORPORATE_BOND = "corporate_bond"
    FRN = "floating_rate_note"
    CONVERTIBLE_BOND = "convertible_bond"
    COMMERCIAL_PAPER = "commercial_paper"
    MTN = "medium_term_note"
    
    # Fixed Income - Structured
    MBS = "mortgage_backed_securities"
    ABS = "asset_backed_securities"
    CDO = "collateralized_debt_obligation"
    CLO = "collateralized_loan_obligation"
    ZERO_COUPON_BOND = "zero_coupon_bond"
    
    # Structured Products
    CALLABLE_SWAP = "callable_swap"
    CANCELABLE_SWAP = "cancelable_swap"
    RANGE_ACCRUAL = "range_accrual"
    SNOWBALL = "snowball"



class DayCountConvention(Enum):
    """Day count conventions for interest calculations."""
    ACT_360 = "ACT/360"
    ACT_365 = "ACT/365"
    ACT_365_FIXED = "ACT/365F"
    ACT_ACT = "ACT/ACT"
    THIRTY_360 = "30/360"
    THIRTY_360_US = "30/360 US"
    THIRTY_E_360 = "30E/360"
    BUS_252 = "BUS/252"


class PaymentFrequency(Enum):
    """Payment frequency for periodic payments."""
    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"
    QUARTERLY = "Q"
    SEMI_ANNUAL = "S"
    ANNUAL = "A"
    AT_MATURITY = "T"
    ZERO = "Z"


class BusinessDayConvention(Enum):
    """Business day adjustment conventions."""
    FOLLOWING = "F"
    MODIFIED_FOLLOWING = "MF"
    PRECEDING = "P"
    MODIFIED_PRECEDING = "MP"
    UNADJUSTED = "U"


class OptionType(Enum):
    """Option type for options products."""
    CALL = "call"
    PUT = "put"


class OptionStyle(Enum):
    """Exercise style for options."""
    EUROPEAN = "european"
    AMERICAN = "american"
    BERMUDAN = "bermudan"


class BarrierType(Enum):
    """Barrier type for barrier options."""
    UP_IN = "up_in"
    UP_OUT = "up_out"
    DOWN_IN = "down_in"
    DOWN_OUT = "down_out"
    DOUBLE_IN = "double_in"
    DOUBLE_OUT = "double_out"


class SettlementType(Enum):
    """Settlement type for derivatives."""
    PHYSICAL = "physical"
    CASH = "cash"


class Currency(Enum):
    """Major currencies supported."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CHF = "CHF"
    CAD = "CAD"
    AUD = "AUD"
    NZD = "NZD"
    SEK = "SEK"
    NOK = "NOK"
    DKK = "DKK"
    SGD = "SGD"
    HKD = "HKD"
    CNY = "CNY"
    CNH = "CNH"
    KRW = "KRW"
    INR = "INR"
    BRL = "BRL"
    MXN = "MXN"
    ZAR = "ZAR"


class FloatingRateIndex(Enum):
    """Floating rate indices."""
    # USD
    SOFR = "SOFR"
    TERM_SOFR = "TERM_SOFR"
    FED_FUNDS = "FED_FUNDS"
    USD_LIBOR_3M = "USD_LIBOR_3M"  # Legacy
    
    # EUR
    EURIBOR_1M = "EURIBOR_1M"
    EURIBOR_3M = "EURIBOR_3M"
    EURIBOR_6M = "EURIBOR_6M"
    ESTR = "ESTR"
    
    # GBP
    SONIA = "SONIA"
    GBP_LIBOR_3M = "GBP_LIBOR_3M"  # Legacy
    
    # JPY
    TONA = "TONA"
    TIBOR_3M = "TIBOR_3M"
    
    # CHF
    SARON = "SARON"
    
    # Other
    BBSW = "BBSW"           # AUD
    CDOR = "CDOR"           # CAD
    CORRA = "CORRA"         # CAD
    HIBOR = "HIBOR"         # HKD
    SIBOR = "SIBOR"         # SGD
    SORA = "SORA"           # SGD


class CreditEventType(Enum):
    """Credit event types for credit derivatives."""
    BANKRUPTCY = "bankruptcy"
    FAILURE_TO_PAY = "failure_to_pay"
    RESTRUCTURING = "restructuring"
    OBLIGATION_ACCELERATION = "obligation_acceleration"
    OBLIGATION_DEFAULT = "obligation_default"
    REPUDIATION = "repudiation"


class CommodityType(Enum):
    """Commodity types for commodity derivatives."""
    # Energy
    CRUDE_OIL_WTI = "WTI"
    CRUDE_OIL_BRENT = "BRENT"
    NATURAL_GAS = "NG"
    HEATING_OIL = "HO"
    GASOLINE = "RBOB"
    
    # Metals
    GOLD = "XAU"
    SILVER = "XAG"
    PLATINUM = "XPT"
    PALLADIUM = "XPD"
    COPPER = "HG"
    ALUMINUM = "AL"
    
    # Agriculture
    CORN = "C"
    WHEAT = "W"
    SOYBEANS = "S"
    SUGAR = "SB"
    COFFEE = "KC"
    COTTON = "CT"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class MarketData:
    """Container for market data required for pricing."""
    valuation_date: date
    discount_curve: Dict[float, float] = field(default_factory=dict)
    forward_curves: Dict[str, Dict[float, float]] = field(default_factory=dict)
    fx_spots: Dict[str, float] = field(default_factory=dict)
    volatility_surfaces: Dict[str, Any] = field(default_factory=dict)
    credit_curves: Dict[str, Dict[float, float]] = field(default_factory=dict)
    correlation_matrix: Optional[np.ndarray] = None
    dividend_curves: Dict[str, Dict[float, float]] = field(default_factory=dict)
    equity_prices: Dict[str, float] = field(default_factory=dict)
    bond_prices: Dict[str, float] = field(default_factory=dict)
    reference_rates: Dict[str, float] = field(default_factory=dict)
    commodity_prices: Dict[str, float] = field(default_factory=dict)


@dataclass
class PricingResult:
    """Result of a product pricing calculation."""
    npv: float                               # Net Present Value
    currency: str                            # Result currency
    components: Dict[str, float] = field(default_factory=dict)
    greeks: Dict[str, float] = field(default_factory=dict)
    cash_flows: List[Dict[str, Any]] = field(default_factory=list)
    risk_measures: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CCRExposureProfile:
    """CCR exposure profile for a product."""
    time_grid: List[float]                   # Time points in years
    expected_exposure: List[float]           # EE profile
    potential_future_exposure: List[float]   # PFE profile
    effective_ee: List[float]                # Effective EE
    peak_exposure: float                     # Peak PFE
    epe: float                               # Expected Positive Exposure
    effective_epe: float                     # Effective EPE
    cva: float                               # Credit Valuation Adjustment
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SACCRExposure:
    """SA-CCR exposure calculation result."""
    replacement_cost: float                  # RC
    pfe_add_on: float                        # PFE add-on
    ead: float                               # EAD = 1.4 × (RC + PFE)
    asset_class: AssetClass
    hedging_set_contributions: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Base Product Class
# =============================================================================

class BaseProduct(ABC):
    """
    Abstract base class for all derivative products.
    
    All products must implement:
    - price(): Calculate NPV and Greeks
    - calculate_ccr_exposure(): Compute CCR exposure profile
    - calculate_saccr(): Compute SA-CCR exposure
    - to_dict(): Serialize to dictionary
    """
    
    def __init__(
        self,
        trade_id: str,
        product_type: ProductType,
        asset_class: AssetClass,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,
        currency: Currency,
        counterparty_id: str,
        netting_set_id: Optional[str] = None,
        csa_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize base product.
        
        Args:
            trade_id: Unique trade identifier
            product_type: Type of derivative product
            asset_class: Asset class classification
            trade_date: Trade execution date
            effective_date: Effective/start date
            maturity_date: Maturity/end date
            notional: Notional principal amount
            currency: Notional currency
            counterparty_id: Counterparty identifier
            netting_set_id: Netting set identifier
            csa_id: CSA/collateral agreement identifier
            **kwargs: Additional product-specific parameters
        """
        self.trade_id = trade_id
        self.product_type = product_type
        self.asset_class = asset_class
        self.trade_date = trade_date
        self.effective_date = effective_date
        self.maturity_date = maturity_date
        self.notional = notional
        self.currency = currency
        self.counterparty_id = counterparty_id
        self.netting_set_id = netting_set_id or counterparty_id
        self.csa_id = csa_id
        self.additional_params = kwargs
    
    @abstractmethod
    def price(self, market_data: MarketData) -> PricingResult:
        """
        Calculate NPV and Greeks for the product.
        
        Args:
            market_data: Market data for valuation
            
        Returns:
            PricingResult with NPV, Greeks, and cash flows
        """
        pass
    
    @abstractmethod
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """
        Calculate CCR exposure profile using Monte Carlo simulation.
        
        Args:
            market_data: Market data for simulation
            time_horizon: Exposure horizon in years
            num_scenarios: Number of Monte Carlo scenarios
            confidence_level: Confidence level for PFE
            
        Returns:
            CCRExposureProfile with EE, PFE, and CVA
        """
        pass
    
    @abstractmethod
    def calculate_saccr(
        self,
        market_data: MarketData
    ) -> SACCRExposure:
        """
        Calculate SA-CCR exposure for the product.
        
        Args:
            market_data: Market data for calculation
            
        Returns:
            SACCRExposure with RC, PFE add-on, and EAD
        """
        pass
    
    def risk_factors(self, market_data: MarketData) -> List[Any]:
        """
        Risk factors this product's price depends on.
        
        The default detects dependencies by pricing once against an
        access-recording copy of the market data. Override for products
        where that is too broad or too slow.
        
        Args:
            market_data: Market data the product will be priced against
            
        Returns:
            List of RiskFactorKey
        """
        from ..riskfactors.mapping import detect_risk_factors
        return detect_risk_factors(self, market_data)
    
    def get_remaining_maturity(self, as_of_date: date) -> float:
        """Calculate remaining maturity in years."""
        days = (self.maturity_date - as_of_date).days
        return max(0, days / 365.25)
    
    def get_time_to_effective(self, as_of_date: date) -> float:
        """Calculate time to effective date in years."""
        days = (self.effective_date - as_of_date).days
        return max(0, days / 365.25)
    
    def is_expired(self, as_of_date: date) -> bool:
        """Check if product has expired."""
        return as_of_date >= self.maturity_date
    
    def is_forward_starting(self, as_of_date: date) -> bool:
        """Check if product is forward starting."""
        return as_of_date < self.effective_date
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize product to dictionary."""
        return {
            "trade_id": self.trade_id,
            "product_type": self.product_type.value,
            "asset_class": self.asset_class.value,
            "trade_date": self.trade_date.isoformat(),
            "effective_date": self.effective_date.isoformat(),
            "maturity_date": self.maturity_date.isoformat(),
            "notional": self.notional,
            "currency": self.currency.value,
            "counterparty_id": self.counterparty_id,
            "netting_set_id": self.netting_set_id,
            "csa_id": self.csa_id,
            **self.additional_params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseProduct':
        """Deserialize product from dictionary."""
        raise NotImplementedError("Subclasses must implement from_dict")
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"trade_id={self.trade_id}, "
            f"type={self.product_type.value}, "
            f"notional={self.notional:,.2f} {self.currency.value}, "
            f"maturity={self.maturity_date})"
        )


# =============================================================================
# SA-CCR Parameters
# =============================================================================

class SACCRParameters:
    """SA-CCR regulatory parameters and add-on factors."""
    
    # Supervisory factor (SF) by asset class and sub-class
    SUPERVISORY_FACTORS = {
        # Interest Rate
        (AssetClass.INTEREST_RATE, None): 0.005,
        
        # FX
        (AssetClass.FX, None): 0.04,
        
        # Credit (single name)
        (AssetClass.CREDIT, "AAA"): 0.0038,
        (AssetClass.CREDIT, "AA"): 0.0038,
        (AssetClass.CREDIT, "A"): 0.0042,
        (AssetClass.CREDIT, "BBB"): 0.0054,
        (AssetClass.CREDIT, "BB"): 0.0106,
        (AssetClass.CREDIT, "B"): 0.0106,
        (AssetClass.CREDIT, "CCC"): 0.0106,
        (AssetClass.CREDIT, "IG_INDEX"): 0.0038,
        (AssetClass.CREDIT, "SG_INDEX"): 0.0106,
        
        # Equity (single name)
        (AssetClass.EQUITY, "SINGLE"): 0.32,
        (AssetClass.EQUITY, "INDEX"): 0.20,
        
        # Commodity
        (AssetClass.COMMODITY, "ELECTRICITY"): 0.40,
        (AssetClass.COMMODITY, "OIL_GAS"): 0.18,
        (AssetClass.COMMODITY, "METALS"): 0.18,
        (AssetClass.COMMODITY, "AGRICULTURAL"): 0.18,
        (AssetClass.COMMODITY, "OTHER"): 0.18,
    }
    
    # Supervisory option volatility by asset class
    SUPERVISORY_VOLATILITY = {
        AssetClass.INTEREST_RATE: 0.50,
        AssetClass.FX: 0.15,
        AssetClass.CREDIT: 1.00,
        AssetClass.EQUITY: 1.20,
        AssetClass.COMMODITY: 1.50,
    }
    
    # Correlation parameters
    CORRELATIONS = {
        AssetClass.INTEREST_RATE: {
            "same_currency": 1.0,
            "different_currency": 0.5,
        },
        AssetClass.FX: {
            "same_pair": 1.0,
            "different_pair": 0.0,  # More complex in practice
        },
        AssetClass.CREDIT: {
            "same_entity": 1.0,
            "same_sector": 0.8,
            "different_sector": 0.5,
        },
        AssetClass.EQUITY: {
            "same_entity": 1.0,
            "same_sector": 0.8,
            "different_sector": 0.5,
        },
        AssetClass.COMMODITY: {
            "same_commodity": 1.0,
            "same_type": 0.9,
            "different_type": 0.4,
        },
    }
    
    # Maturity factor parameters
    MATURITY_FACTOR_FLOOR = 10 / 252  # 10 business days
    
    # Alpha multiplier
    ALPHA = 1.4
    
    @classmethod
    def get_supervisory_factor(
        cls,
        asset_class: AssetClass,
        sub_class: Optional[str] = None
    ) -> float:
        """Get supervisory factor for asset class."""
        key = (asset_class, sub_class)
        if key in cls.SUPERVISORY_FACTORS:
            return cls.SUPERVISORY_FACTORS[key]
        return cls.SUPERVISORY_FACTORS.get((asset_class, None), 0.05)
    
    @classmethod
    def calculate_maturity_factor(cls, maturity: float, mpor: float = 10/252) -> float:
        """Calculate SA-CCR maturity factor."""
        effective_maturity = max(cls.MATURITY_FACTOR_FLOOR, min(maturity, 1.0))
        return np.sqrt(min(effective_maturity, 1.0))


# =============================================================================
# Utility Functions
# =============================================================================

def year_fraction(
    start_date: date,
    end_date: date,
    convention: DayCountConvention = DayCountConvention.ACT_365
) -> float:
    """
    Calculate year fraction between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
        convention: Day count convention
        
    Returns:
        Year fraction as float
    """
    days = (end_date - start_date).days
    
    if convention == DayCountConvention.ACT_360:
        return days / 360
    elif convention == DayCountConvention.ACT_365:
        return days / 365
    elif convention == DayCountConvention.ACT_365_FIXED:
        return days / 365
    elif convention == DayCountConvention.ACT_ACT:
        return days / 365.25
    elif convention in [DayCountConvention.THIRTY_360, 
                        DayCountConvention.THIRTY_360_US,
                        DayCountConvention.THIRTY_E_360]:
        # Simplified 30/360 calculation
        d1 = min(start_date.day, 30)
        d2 = min(end_date.day, 30) if d1 == 30 else end_date.day
        return (
            360 * (end_date.year - start_date.year) +
            30 * (end_date.month - start_date.month) +
            (d2 - d1)
        ) / 360
    else:
        return days / 365


def curve_value(
    curve: Dict[float, float],
    time: float,
    default: float = 0.05
) -> float:
    """
    Read a tenor curve at any time point.
    
    Linear interpolation between pillars, flat extrapolation outside them.
    Returns `default` only when the curve is empty.
    
    Args:
        curve: Mapping of tenor (years) to value (e.g. zero rate)
        time: Time point in years
        default: Value used when the curve has no pillars
        
    Returns:
        Curve value at `time`
    """
    if not curve:
        return default
    tenors = sorted(curve)
    if time <= tenors[0]:
        return curve[tenors[0]]
    if time >= tenors[-1]:
        return curve[tenors[-1]]
    i = bisect_right(tenors, time)
    t0, t1 = tenors[i - 1], tenors[i]
    w = (time - t0) / (t1 - t0)
    return curve[t0] + w * (curve[t1] - curve[t0])


def discount_factor(rate: float, time: float) -> float:
    """Calculate discount factor from rate and time."""
    return np.exp(-rate * time)


def forward_rate(
    df_start: float,
    df_end: float,
    start_time: float,
    end_time: float
) -> float:
    """Calculate forward rate from discount factors."""
    if end_time <= start_time:
        return 0.0
    return (df_start / df_end - 1) / (end_time - start_time)


def black_scholes_call(
    spot: float,
    strike: float,
    time: float,
    rate: float,
    volatility: float,
    dividend: float = 0.0
) -> Tuple[float, Dict[str, float]]:
    """
    Black-Scholes call option price and Greeks.
    
    Returns:
        Tuple of (price, greeks_dict)
    """
    from scipy.stats import norm
    
    if time <= 0:
        return max(0, spot - strike), {"delta": 1.0 if spot > strike else 0.0}
    
    d1 = (np.log(spot / strike) + (rate - dividend + 0.5 * volatility**2) * time) / (volatility * np.sqrt(time))
    d2 = d1 - volatility * np.sqrt(time)
    
    price = (spot * np.exp(-dividend * time) * norm.cdf(d1) - 
             strike * np.exp(-rate * time) * norm.cdf(d2))
    
    greeks = {
        "delta": np.exp(-dividend * time) * norm.cdf(d1),
        "gamma": np.exp(-dividend * time) * norm.pdf(d1) / (spot * volatility * np.sqrt(time)),
        "vega": spot * np.exp(-dividend * time) * norm.pdf(d1) * np.sqrt(time) / 100,
        "theta": (-spot * np.exp(-dividend * time) * norm.pdf(d1) * volatility / (2 * np.sqrt(time)) -
                  rate * strike * np.exp(-rate * time) * norm.cdf(d2) +
                  dividend * spot * np.exp(-dividend * time) * norm.cdf(d1)) / 365,
        "rho": strike * time * np.exp(-rate * time) * norm.cdf(d2) / 100,
    }
    
    return price, greeks


def black_scholes_put(
    spot: float,
    strike: float,
    time: float,
    rate: float,
    volatility: float,
    dividend: float = 0.0
) -> Tuple[float, Dict[str, float]]:
    """
    Black-Scholes put option price and Greeks.
    
    Returns:
        Tuple of (price, greeks_dict)
    """
    from scipy.stats import norm
    
    if time <= 0:
        return max(0, strike - spot), {"delta": -1.0 if spot < strike else 0.0}
    
    d1 = (np.log(spot / strike) + (rate - dividend + 0.5 * volatility**2) * time) / (volatility * np.sqrt(time))
    d2 = d1 - volatility * np.sqrt(time)
    
    price = (strike * np.exp(-rate * time) * norm.cdf(-d2) - 
             spot * np.exp(-dividend * time) * norm.cdf(-d1))
    
    greeks = {
        "delta": np.exp(-dividend * time) * (norm.cdf(d1) - 1),
        "gamma": np.exp(-dividend * time) * norm.pdf(d1) / (spot * volatility * np.sqrt(time)),
        "vega": spot * np.exp(-dividend * time) * norm.pdf(d1) * np.sqrt(time) / 100,
        "theta": (-spot * np.exp(-dividend * time) * norm.pdf(d1) * volatility / (2 * np.sqrt(time)) +
                  rate * strike * np.exp(-rate * time) * norm.cdf(-d2) -
                  dividend * spot * np.exp(-dividend * time) * norm.cdf(-d1)) / 365,
        "rho": -strike * time * np.exp(-rate * time) * norm.cdf(-d2) / 100,
    }
    
    return price, greeks


def bachelier_call(
    forward: float,
    strike: float,
    time: float,
    volatility: float,
    discount_factor: float
) -> float:
    """Bachelier (normal) model call option price."""
    from scipy.stats import norm
    
    if time <= 0:
        return max(0, forward - strike) * discount_factor
    
    std = volatility * np.sqrt(time)
    d = (forward - strike) / std
    
    return discount_factor * (
        (forward - strike) * norm.cdf(d) + std * norm.pdf(d)
    )


def bachelier_put(
    forward: float,
    strike: float,
    time: float,
    volatility: float,
    discount_factor: float
) -> float:
    """Bachelier (normal) model put option price."""
    from scipy.stats import norm
    
    if time <= 0:
        return max(0, strike - forward) * discount_factor
    
    std = volatility * np.sqrt(time)
    d = (forward - strike) / std
    
    return discount_factor * (
        (strike - forward) * norm.cdf(-d) + std * norm.pdf(d)
    )
