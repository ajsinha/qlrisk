"""
QLRisk - Fixed Income Products v2.3.1
====================================================

Fixed income products including government bonds, corporate bonds, 
structured products, and total return swaps.

Products:
- Government: TreasuryBill, TreasuryNote, TreasuryBond, TIPS, UKGilt, GermanBund, JGB, FrenchOAT
- Corporate: MunicipalBond, AgencyBond, CorporateBond, FloatingRateNote
- Credit: ConvertibleBond, CommercialPaper, MediumTermNote
- Structured: MBS, ABS, CDO, CLO, ZeroCouponBond
- TRS: BondTRS (Bond Total Return Swap)

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

__version__ = "2.3.1"

from .treasury_bill import TreasuryBill
from .treasury_note import TreasuryNote
from .treasury_bond import TreasuryBond
from .tips import TIPS
from .uk_gilt import UKGilt
from .german_bund import GermanBund
from .jgb import JGB
from .french_oat import FrenchOAT
from .municipal_bond import MunicipalBond
from .agency_bond import AgencyBond
from .corporate_bond import CorporateBond
from .floating_rate_note import FloatingRateNote
from .convertible_bond import ConvertibleBond
from .commercial_paper import CommercialPaper
from .medium_term_note import MediumTermNote
from .mbs import MBS
from .abs import ABS
from .cdo import CDO
from .clo import CLO
from .zero_coupon_bond import ZeroCouponBond
from .bond_trs import (
    BondTRS, 
    BondTRSTerms, 
    BondTRSUnderlyingType,
    BondTRSReturnType,
    BondTRSResetType
)

__all__ = [
    "__version__",
    # Government
    "TreasuryBill",
    "TreasuryNote",
    "TreasuryBond",
    "TIPS",
    "UKGilt",
    "GermanBund",
    "JGB",
    "FrenchOAT",
    # Corporate/Municipal
    "MunicipalBond",
    "AgencyBond",
    "CorporateBond",
    "FloatingRateNote",
    "ConvertibleBond",
    "CommercialPaper",
    "MediumTermNote",
    # Structured
    "MBS",
    "ABS",
    "CDO",
    "CLO",
    "ZeroCouponBond",
    # TRS
    "BondTRS",
    "BondTRSTerms",
    "BondTRSUnderlyingType",
    "BondTRSReturnType",
    "BondTRSResetType",
]
