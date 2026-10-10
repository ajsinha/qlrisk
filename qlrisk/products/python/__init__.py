"""
QLRisk - Python Products v2.1.0
==============================================

Pure Python implementations of 90+ financial products across all asset classes.

Asset Classes:
- Interest Rate (8): IRS, OIS, FRA, Cap, Floor, Swaption, Basis Swap
- FX (6): Forward, Swap, Option, Barrier, NDF, Digital
- Credit (4): CDS, CDS Index, TRS, CLN
- Equity (6): Swap, Option, Forward, Variance, Dividend, EquityTRS
- Commodity (3): Swap, Option, Forward
- Cross-Currency (3): XCCY Swap, Basis, MTM
- Repo (4): Repo, Reverse Repo, Securities Lending, Buy/Sell Back
- Money Market (7): CD, BA, Eurodollar, Fed Funds, MMF, TD, Discount Note
- Stocks (8): Common, ADR, GDR, Preferred, Warrant, ETF, MF, Index
- Alternatives (8): Crypto (3), REIT, Carbon (2), PE, HF
- Futures (6): Index, IR, Bond, VIX, SSF, Commodity
- Fixed Income (21): Treasuries, Gilts, Bunds, MBS, CDO, CLO, BondTRS
- SFT (4): MarginLoan, CollateralSwap, TriPartyRepo, PrimeBrokerage

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

__version__ = "2.1.0"

# Interest Rate (8)
from .interest_rate import (
    InterestRateSwap, IRSLeg, OvernightIndexSwap, ForwardRateAgreement,
    InterestRateCap, InterestRateFloor, Swaption, BasisSwap
)

# FX (6)
from .fx import (
    FXForward, FXSwap, FXOption, FXBarrierOption, 
    NonDeliverableForward, FXDigitalOption
)

# Credit (4)
from .credit import (
    CreditDefaultSwap, CDSIndex, TotalReturnSwap, CreditLinkedNote
)

# Equity Derivatives (6)
from .equity import (
    EquitySwap, EquityOption, EquityForward, VarianceSwap, DividendSwap,
    EquityTRS, EquityTRSType, EquityTRSTerms
)

# Commodity (3)
from .commodity import CommoditySwap, CommodityOption, CommodityForward

# Cross-Currency (3)
from .cross_currency import (
    CrossCurrencySwap, CrossCurrencyBasisSwap, MTMCrossCurrencySwap
)

# Repo (4)
from .repo import Repo, ReverseRepo, SecuritiesLending, BuySellBack

# Money Market (7)
from .money_market import (
    CertificateOfDeposit, BankersAcceptance, EurodollarDeposit,
    FederalFunds, MoneyMarketFund, TimeDeposit, DiscountNote
)

# Stocks (8)
from .stocks import (
    CommonStock, ADR, GDR, PreferredStock, Warrant, ETF, MutualFund, IndexPosition
)

# Alternatives (8)
from .alternatives import (
    CryptoSpot, CryptoFuture, CryptoPerpetual, REIT,
    CarbonCredit, CarbonFuture, PrivateEquityInterest, HedgeFundInterest
)

# Futures (6)
from .futures import (
    IndexFuture, InterestRateFuture, BondFuture, VIXFuture, SingleStockFuture,
    CommodityFuture, CommodityType, CommodityFutureTerms, CommoditySubClass
)

# Fixed Income (21)
from .fixed_income import (
    TreasuryBill, TreasuryNote, TreasuryBond, TIPS,
    UKGilt, GermanBund, JGB, FrenchOAT,
    MunicipalBond, AgencyBond, CorporateBond,
    FloatingRateNote, ConvertibleBond, CommercialPaper, MediumTermNote,
    MBS, ABS, CDO, CLO, ZeroCouponBond,
    BondTRS, BondTRSTerms, BondTRSUnderlyingType, BondTRSReturnType, BondTRSResetType
)

# Securities Financing Transactions - SFT (7)
from .sft import (
    MarginLoan, MarginLoanTerms, MarginLoanType,
    MarginLending, LoanPurpose,
    CollateralSwap, CollateralQuality, CollateralLeg,
    TriPartyRepo, TriPartyRepoTerms, TriPartyAgent,
    PrimeBrokerage, PrimeBrokerageTerms, PBServiceType,
    SecuritiesBorrowing,
    StockLoan, StockLoanType, StockLoanTerms
)

__all__ = [
    "__version__",
    # Interest Rate (8)
    "InterestRateSwap", "IRSLeg", "OvernightIndexSwap", "ForwardRateAgreement",
    "InterestRateCap", "InterestRateFloor", "Swaption", "BasisSwap",
    # FX (6)
    "FXForward", "FXSwap", "FXOption", "FXBarrierOption", 
    "NonDeliverableForward", "FXDigitalOption",
    # Credit (4)
    "CreditDefaultSwap", "CDSIndex", "TotalReturnSwap", "CreditLinkedNote",
    # Equity (6)
    "EquitySwap", "EquityOption", "EquityForward", "VarianceSwap", "DividendSwap",
    "EquityTRS", "EquityTRSType", "EquityTRSTerms",
    # Commodity (3)
    "CommoditySwap", "CommodityOption", "CommodityForward",
    # Cross-Currency (3)
    "CrossCurrencySwap", "CrossCurrencyBasisSwap", "MTMCrossCurrencySwap",
    # Repo (4)
    "Repo", "ReverseRepo", "SecuritiesLending", "BuySellBack",
    # Money Market (7)
    "CertificateOfDeposit", "BankersAcceptance", "EurodollarDeposit",
    "FederalFunds", "MoneyMarketFund", "TimeDeposit", "DiscountNote",
    # Stocks (8)
    "CommonStock", "ADR", "GDR", "PreferredStock", 
    "Warrant", "ETF", "MutualFund", "IndexPosition",
    # Alternatives (8)
    "CryptoSpot", "CryptoFuture", "CryptoPerpetual", "REIT",
    "CarbonCredit", "CarbonFuture", "PrivateEquityInterest", "HedgeFundInterest",
    # Futures (6)
    "IndexFuture", "InterestRateFuture", "BondFuture", "VIXFuture", "SingleStockFuture",
    "CommodityFuture", "CommodityType", "CommodityFutureTerms", "CommoditySubClass",
    # Fixed Income (21)
    "TreasuryBill", "TreasuryNote", "TreasuryBond", "TIPS",
    "UKGilt", "GermanBund", "JGB", "FrenchOAT",
    "MunicipalBond", "AgencyBond", "CorporateBond",
    "FloatingRateNote", "ConvertibleBond", "CommercialPaper", "MediumTermNote",
    "MBS", "ABS", "CDO", "CLO", "ZeroCouponBond",
    "BondTRS", "BondTRSTerms", "BondTRSUnderlyingType", "BondTRSReturnType", "BondTRSResetType",
    # SFT (7)
    "MarginLoan", "MarginLoanTerms", "MarginLoanType",
    "MarginLending", "LoanPurpose",
    "CollateralSwap", "CollateralQuality", "CollateralLeg",
    "TriPartyRepo", "TriPartyRepoTerms", "TriPartyAgent",
    "PrimeBrokerage", "PrimeBrokerageTerms", "PBServiceType",
    "SecuritiesBorrowing",
    "StockLoan", "StockLoanType", "StockLoanTerms",
]
