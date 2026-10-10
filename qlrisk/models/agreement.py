"""
QLRisk - Agreement Model v1.2.0
==============================================

ISDA and CSA agreement models for OTC derivatives.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid

from .base import ModelBase


class AgreementType(Enum):
    """Type of agreement."""
    ISDA_MASTER = "isda_master"
    CSA = "csa"
    GMRA = "gmra"  # Global Master Repurchase Agreement
    GMSLA = "gmsla"  # Global Master Securities Lending Agreement
    ISDA_CSA = "isda_csa"  # Combined
    

class ISDAVersion(Enum):
    """ISDA Master Agreement version."""
    ISDA_1992 = "1992"
    ISDA_2002 = "2002"


class CSAType(Enum):
    """Type of CSA."""
    BILATERAL = "bilateral"
    ONE_WAY = "one_way"
    VM_ONLY = "vm_only"  # Variation margin only
    VM_IM = "vm_im"  # Variation + Initial margin


class GoverningLaw(Enum):
    """Governing law jurisdiction."""
    NEW_YORK = "new_york"
    ENGLISH = "english"
    JAPANESE = "japanese"
    FRENCH = "french"
    GERMAN = "german"


@dataclass
class ISDAMasterAgreement(ModelBase):
    """ISDA Master Agreement."""
    agreement_id: str = field(default_factory=lambda: f"ISDA-{uuid.uuid4().hex[:8].upper()}")
    version: ISDAVersion = ISDAVersion.ISDA_2002
    party_a: str = ""
    party_b: str = ""
    
    # Key dates
    execution_date: date = field(default_factory=date.today)
    effective_date: date = field(default_factory=date.today)
    
    # Governing law and jurisdiction
    governing_law: GoverningLaw = GoverningLaw.NEW_YORK
    
    # Events of default
    cross_default: bool = True
    cross_default_threshold: float = 0.0
    credit_event_upon_merger: bool = True
    
    # Termination provisions
    automatic_early_termination: bool = False
    
    # Netting
    close_out_netting: bool = True
    payment_netting: bool = True
    
    # Additional terms
    schedule_amendments: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        return bool(self.party_a and self.party_b)


@dataclass
class CSAThreshold:
    """Credit Support Annex thresholds."""
    party: str = ""
    threshold_amount: float = 0.0
    threshold_currency: str = "USD"
    
    # Rating-dependent thresholds
    rating_dependent: bool = False
    threshold_schedule: Dict[str, float] = field(default_factory=dict)
    # e.g., {"AAA": 50000000, "AA": 25000000, "A": 10000000, "BBB": 0}
    
    def get_threshold(self, rating: str = None) -> float:
        """Get applicable threshold."""
        if self.rating_dependent and rating:
            return self.threshold_schedule.get(rating, 0.0)
        return self.threshold_amount


@dataclass
class CreditSupportAnnex(ModelBase):
    """Credit Support Annex (CSA) for collateral terms."""
    csa_id: str = field(default_factory=lambda: f"CSA-{uuid.uuid4().hex[:8].upper()}")
    isda_reference: str = ""  # Reference to ISDA Master
    csa_type: CSAType = CSAType.BILATERAL
    
    # Parties
    party_a: str = ""
    party_b: str = ""
    
    # Key dates
    execution_date: date = field(default_factory=date.today)
    effective_date: date = field(default_factory=date.today)
    
    # Thresholds
    party_a_threshold: CSAThreshold = field(default_factory=CSAThreshold)
    party_b_threshold: CSAThreshold = field(default_factory=CSAThreshold)
    
    # Minimum Transfer Amount
    party_a_mta: float = 500000.0
    party_b_mta: float = 500000.0
    
    # Rounding
    rounding_amount: float = 10000.0
    
    # Valuation
    valuation_agent: str = ""
    valuation_date: str = "each local business day"
    notification_time: str = "1:00 PM"
    
    # Eligible collateral (simplified)
    eligible_currency: List[str] = field(default_factory=lambda: ["USD", "EUR", "GBP"])
    eligible_securities: bool = True
    
    # Transfer timing
    transfer_timing: str = "T+1"
    dispute_resolution_period: int = 2  # business days
    
    # Interest
    interest_rate: str = "Fed Funds"
    interest_period: str = "monthly"
    
    # Rehypothecation
    rehypothecation_allowed: bool = False
    
    def validate(self) -> bool:
        return bool(self.party_a and self.party_b)
    
    def get_threshold(self, party: str, rating: str = None) -> float:
        """Get threshold for a party."""
        if party == self.party_a:
            return self.party_a_threshold.get_threshold(rating)
        elif party == self.party_b:
            return self.party_b_threshold.get_threshold(rating)
        return 0.0
    
    def get_mta(self, party: str) -> float:
        """Get MTA for a party."""
        if party == self.party_a:
            return self.party_a_mta
        elif party == self.party_b:
            return self.party_b_mta
        return 0.0


@dataclass
class InitialMarginCSA(ModelBase):
    """Initial Margin Credit Support Annex."""
    im_csa_id: str = field(default_factory=lambda: f"IMCSA-{uuid.uuid4().hex[:8].upper()}")
    csa_reference: str = ""  # Reference to VM CSA
    
    # Parties
    party_a: str = ""
    party_b: str = ""
    
    # IM calculation method
    calculation_method: str = "ISDA SIMM"  # SIMM, Schedule, Grid
    
    # Thresholds (regulatory: typically 50M EUR)
    im_threshold: float = 50000000.0
    threshold_currency: str = "EUR"
    
    # MTA
    im_mta: float = 500000.0
    
    # Custodian
    party_a_custodian: str = ""
    party_b_custodian: str = ""
    
    # Segregation
    segregation_required: bool = True
    
    def validate(self) -> bool:
        return True


@dataclass
class NettingAgreement(ModelBase):
    """Netting agreement details."""
    netting_id: str = field(default_factory=lambda: f"NET-{uuid.uuid4().hex[:8].upper()}")
    agreement_reference: str = ""
    
    # Netting type
    payment_netting: bool = True
    close_out_netting: bool = True
    cross_product_netting: bool = False
    
    # Scope
    included_products: List[str] = field(default_factory=list)
    excluded_products: List[str] = field(default_factory=list)
    
    # Jurisdictional enforceability
    enforceable_jurisdictions: List[str] = field(default_factory=lambda: ["US", "GB", "DE", "FR", "JP"])
    
    def validate(self) -> bool:
        return True
    
    def is_enforceable(self, jurisdiction: str) -> bool:
        """Check if netting is enforceable in jurisdiction."""
        return jurisdiction in self.enforceable_jurisdictions


__all__ = [
    "AgreementType",
    "ISDAVersion",
    "CSAType",
    "GoverningLaw",
    "ISDAMasterAgreement",
    "CSAThreshold",
    "CreditSupportAnnex",
    "InitialMarginCSA",
    "NettingAgreement",
]
