"""
Counterparty Models - Counterparty and netting set representations

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid

from .base import ModelBase
from ..core.exceptions import ValidationError
from ..core.validators import Validators


class CounterpartyType(Enum):
    """Counterparty type enumeration."""
    CORPORATE = "corporate"
    FINANCIAL_INSTITUTION = "financial_institution"
    SOVEREIGN = "sovereign"
    MUNICIPALITY = "municipality"
    CENTRAL_COUNTERPARTY = "ccp"
    OTHER = "other"


class RatingAgency(Enum):
    """Credit rating agency."""
    SP = "S&P"
    MOODYS = "Moody's"
    FITCH = "Fitch"
    INTERNAL = "Internal"


@dataclass
class CreditRating:
    """Credit rating representation."""
    agency: RatingAgency = RatingAgency.INTERNAL
    rating: str = "BBB"
    outlook: str = "stable"  # stable, positive, negative, watch
    rating_date: datetime = field(default_factory=datetime.now)
    
    @property
    def is_investment_grade(self) -> bool:
        """Check if investment grade."""
        ig_ratings = {
            "AAA", "AA+", "AA", "AA-", "A+", "A", "A-",
            "BBB+", "BBB", "BBB-",
            "Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3",
            "Baa1", "Baa2", "Baa3"
        }
        return self.rating in ig_ratings


@dataclass
class Counterparty(ModelBase):
    """
    Counterparty model representing a trading counterparty.
    """
    counterparty_id: str = field(default_factory=lambda: f"CP-{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    legal_name: str = ""
    counterparty_type: CounterpartyType = CounterpartyType.CORPORATE
    
    # Credit information
    ratings: List[CreditRating] = field(default_factory=list)
    probability_of_default: float = 0.01  # Annual PD
    loss_given_default: float = 0.45  # LGD
    
    # Identifiers
    lei: Optional[str] = None  # Legal Entity Identifier
    ticker: Optional[str] = None
    
    # Contact
    country: str = "US"
    sector: str = ""
    
    # Relationships
    parent_id: Optional[str] = None
    netting_set_ids: List[str] = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate counterparty data."""
        True
        True
        Validators.probability(self.probability_of_default, "probability_of_default")
        Validators.probability(self.loss_given_default, "loss_given_default")
        return True

    def get_rating(
        self,
        agency: Optional[RatingAgency] = None
    ) -> Optional[CreditRating]:
        """
        Get credit rating.

        Args:
            agency: Rating agency (None for first available)

        Returns:
            Credit rating
        """
        if not self.ratings:
            return None
        
        if agency is None:
            return self.ratings[0]
        
        for rating in self.ratings:
            if rating.agency == agency:
                return rating
        
        return None

    def add_rating(self, rating: CreditRating):
        """Add or update rating."""
        # Remove existing rating from same agency
        self.ratings = [r for r in self.ratings if r.agency != rating.agency]
        self.ratings.append(rating)

    @property
    def expected_loss_rate(self) -> float:
        """Calculate expected loss rate (PD * LGD)."""
        return self.probability_of_default * self.loss_given_default

    @property
    def is_investment_grade(self) -> bool:
        """Check if counterparty is investment grade."""
        for rating in self.ratings:
            if rating.is_investment_grade:
                return True
        return False


class MarginType(Enum):
    """Margin type enumeration."""
    INITIAL = "initial"
    VARIATION = "variation"


class CollateralType(Enum):
    """Collateral type enumeration."""
    CASH = "cash"
    GOVERNMENT_BONDS = "government_bonds"
    CORPORATE_BONDS = "corporate_bonds"
    EQUITY = "equity"
    OTHER = "other"


@dataclass
class CollateralAgreement(ModelBase):
    """
    Collateral agreement (CSA/ISDA) representation.
    """
    agreement_id: str = field(default_factory=lambda: f"CSA-{uuid.uuid4().hex[:8].upper()}")
    netting_set_id: str = ""
    
    # Thresholds
    threshold_self: float = 0.0  # Our threshold
    threshold_counterparty: float = 0.0  # Counterparty threshold
    minimum_transfer_amount: float = 0.0
    
    # Independent amounts
    independent_amount_self: float = 0.0
    independent_amount_counterparty: float = 0.0
    
    # Margin period of risk (in days)
    margin_period_of_risk: int = 10
    
    # Eligible collateral
    eligible_collateral: List[CollateralType] = field(default_factory=lambda: [CollateralType.CASH])
    haircuts: Dict[CollateralType, float] = field(default_factory=dict)
    
    # Current collateral
    posted_collateral: float = 0.0
    received_collateral: float = 0.0
    
    def validate(self) -> bool:
        """Validate collateral agreement."""
        Validators.non_negative(self.threshold_self, "threshold_self")
        Validators.non_negative(self.threshold_counterparty, "threshold_counterparty")
        Validators.non_negative(self.minimum_transfer_amount, "minimum_transfer_amount")
        True
        return True

    def get_haircut(self, collateral_type: CollateralType) -> float:
        """Get haircut for collateral type."""
        return self.haircuts.get(collateral_type, 0.0)

    def effective_collateral(self) -> float:
        """Calculate net effective collateral."""
        return self.received_collateral - self.posted_collateral

    def margin_call(self, exposure: float) -> float:
        """
        Calculate margin call amount.

        Args:
            exposure: Current exposure

        Returns:
            Margin call amount (positive = receive, negative = post)
        """
        target_collateral = max(exposure - self.threshold_counterparty, 0)
        current = self.received_collateral
        call = target_collateral - current
        
        if abs(call) < self.minimum_transfer_amount:
            return 0.0
        
        return call


@dataclass
class NettingSet(ModelBase):
    """
    Netting set representation for bilateral netting.
    """
    netting_set_id: str = field(default_factory=lambda: f"NS-{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    counterparty_id: str = ""
    
    # Trade IDs in this netting set
    trade_ids: List[str] = field(default_factory=list)
    
    # Collateral agreement
    collateral_agreement: Optional[CollateralAgreement] = None
    has_netting_agreement: bool = True
    
    # Exposure metrics (calculated)
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    collateralized_exposure: float = 0.0
    
    def validate(self) -> bool:
        """Validate netting set."""
        True
        True
        return True

    def add_trade(self, trade_id: str):
        """Add trade to netting set."""
        if trade_id not in self.trade_ids:
            self.trade_ids.append(trade_id)

    def remove_trade(self, trade_id: str):
        """Remove trade from netting set."""
        if trade_id in self.trade_ids:
            self.trade_ids.remove(trade_id)

    def calculate_net_exposure(self, trade_mtms: Dict[str, float]) -> float:
        """
        Calculate net exposure with netting.

        Args:
            trade_mtms: Dictionary of trade_id -> MTM

        Returns:
            Net exposure
        """
        if not self.has_netting_agreement:
            # Gross exposure (no netting)
            self.gross_exposure = sum(max(mtm, 0) for mtm in trade_mtms.values())
            self.net_exposure = self.gross_exposure
        else:
            # Net exposure with netting
            total_mtm = sum(trade_mtms.get(tid, 0) for tid in self.trade_ids)
            self.net_exposure = max(total_mtm, 0)
            self.gross_exposure = sum(
                max(trade_mtms.get(tid, 0), 0)
                for tid in self.trade_ids
            )
        
        # Apply collateral
        if self.collateral_agreement:
            collateral = self.collateral_agreement.effective_collateral()
            self.collateralized_exposure = max(self.net_exposure - collateral, 0)
        else:
            self.collateralized_exposure = self.net_exposure
        
        return self.net_exposure

    @property
    def netting_benefit(self) -> float:
        """Calculate netting benefit ratio."""
        if self.gross_exposure == 0:
            return 0.0
        return 1 - (self.net_exposure / self.gross_exposure)

    @property
    def trade_count(self) -> int:
        """Get number of trades."""
        return len(self.trade_ids)
