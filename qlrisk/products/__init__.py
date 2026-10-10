"""
QLRisk - Products Module v2.0.0
==============================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.

---

Complete product implementations for QLRisk.

Total Products: 81 across 12 asset classes

Python Implementations (81 products):
- Interest Rate (8): IRS, OIS, FRA, Cap, Floor, Swaption, Basis Swap, IRSLeg
- FX (6): Forward, Swap, Option, Barrier, NDF, Digital
- Credit (4): CDS, CDS Index, TRS, Credit Linked Note
- Equity (5): Swap, Option, Forward, Variance Swap, Dividend Swap
- Commodity (3): Swap, Option, Forward
- Cross-Currency (3): XCCY Swap, Basis Swap, MTM Swap
- Repo (4): Repo, Reverse Repo, Securities Lending, Buy/Sell Back
- Money Market (7): CD, BA, Eurodollar, Fed Funds, MMF, Time Deposit, Discount Note
- Stocks (8): Common, ADR, GDR, Preferred, Warrant, ETF, Mutual Fund, Index Position
- Alternatives (8): Crypto (Spot/Future/Perpetual), REIT, Carbon, PE, Hedge Fund
- Futures (5): Index, IR, Bond, VIX, Single Stock
- Fixed Income (20): Treasuries, Gilts, Bunds, JGB, OAT, Muni, Agency, Corporate,
                     FRN, Convertible, CP, MTN, MBS, ABS, CDO, CLO, Zero Coupon

QuantLib Implementations (13 products):
- Interest Rate: IRS, Swaption, Cap, Floor
- FX: Forward, Option
- Fixed Income: Fixed Rate Bond, Floating Rate Bond, Zero Coupon Bond
"""

__version__ = "2.0.0"

from .base import (
    BaseProduct, AssetClass, Currency,
    DayCountConvention, PaymentFrequency, BusinessDayConvention,
    OptionType, OptionStyle, BarrierType, SettlementType,
    FloatingRateIndex,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction, discount_factor
)

from .product_types import ProductType

# Import all Python products
from .python import *

# Import QuantLib products (if available)
try:
    from .qlib import (
        QUANTLIB_AVAILABLE,
        InterestRateSwapQL, SwaptionQL, InterestRateCapQL, InterestRateFloorQL,
        FXForwardQL, FXOptionQL,
        FixedRateBondQL, FloatingRateBondQL, ZeroCouponBondQL,
    )
except ImportError:
    QUANTLIB_AVAILABLE = False

__all__ = [
    "__version__",
    # Base
    "BaseProduct", "AssetClass", "Currency", "ProductType",
    "DayCountConvention", "PaymentFrequency", "BusinessDayConvention",
    "OptionType", "OptionStyle", "BarrierType", "SettlementType",
    "FloatingRateIndex",
    "MarketData", "PricingResult", "CCRExposureProfile", "SACCRExposure",
    "SACCRParameters", "year_fraction", "discount_factor",
    # QuantLib
    "QUANTLIB_AVAILABLE",
]
