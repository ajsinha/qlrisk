"""
QLRisk - Securities Financing Transactions (SFT) v2.0.0
======================================================================

Securities Financing Transactions product implementations.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

SFT products are collateralized transactions used for financing and 
securities borrowing/lending purposes.

Products:
- MarginLoan: Margin lending against securities collateral
- MarginLending: Securities-based lending facility  
- CollateralSwap: Exchange of collateral for other securities
- TriPartyRepo: Tri-party repurchase agreement
- PrimeBrokerage: Prime brokerage financing arrangements
- SecuritiesBorrowing: Securities borrowing arrangement
- StockLoan: Stock lending/borrowing arrangement

Related products (in repo module):
- Repo, ReverseRepo, SecuritiesLending, BuySellBack

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

__version__ = "2.0.0"

from .margin_loan import (
    MarginLoan, 
    MarginLoanTerms, 
    MarginLoanType,
    CollateralCategory,
    CollateralPosition as MLCollateralPosition
)

from .margin_lending import (
    MarginLending,
    LoanPurpose,
    CollateralPosition
)

from .collateral_swap import (
    CollateralSwap, 
    CollateralQuality,
    CollateralLeg
)

from .tri_party_repo import (
    TriPartyRepo, 
    TriPartyRepoTerms, 
    TriPartyAgent,
    CollateralSchedule
)

from .prime_brokerage import (
    PrimeBrokerage, 
    PrimeBrokerageTerms, 
    PBServiceType,
    PBAccountType,
    PBCollateralType,
    PBPosition
)

from .securities_borrowing import SecuritiesBorrowing

from .stock_loan import (
    StockLoan,
    StockLoanType,
    StockLoanTerms,
    LoanCollateralType,
    DividendTreatment
)

__all__ = [
    "__version__",
    # Margin Loan
    "MarginLoan",
    "MarginLoanTerms",
    "MarginLoanType",
    "CollateralCategory",
    "MLCollateralPosition",
    # Margin Lending
    "MarginLending",
    "LoanPurpose",
    "CollateralPosition",
    # Collateral Swap
    "CollateralSwap",
    "CollateralQuality",
    "CollateralLeg",
    # Tri-Party Repo
    "TriPartyRepo",
    "TriPartyRepoTerms",
    "TriPartyAgent",
    "CollateralSchedule",
    # Prime Brokerage
    "PrimeBrokerage",
    "PrimeBrokerageTerms",
    "PBServiceType",
    "PBAccountType",
    "PBCollateralType",
    "PBPosition",
    # Securities Borrowing
    "SecuritiesBorrowing",
    # Stock Loan
    "StockLoan",
    "StockLoanType",
    "StockLoanTerms",
    "LoanCollateralType",
    "DividendTreatment",
]
