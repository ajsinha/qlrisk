"""
QLRisk - Collateral Model v1.2.0
===============================================

Detailed collateral management models including:
- Eligible collateral types
- Haircut schedules
- Collateral valuation
- Margin calls

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid

from .base import ModelBase


class CollateralAssetType(Enum):
    """Type of collateral asset."""
    CASH = "cash"
    GOVERNMENT_BOND = "government_bond"
    CORPORATE_BOND = "corporate_bond"
    EQUITY = "equity"
    GOLD = "gold"
    LETTER_OF_CREDIT = "letter_of_credit"
    OTHER = "other"


class CollateralCurrency(Enum):
    """Major currencies for collateral."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CHF = "CHF"
    CAD = "CAD"
    AUD = "AUD"


# Standard regulatory haircuts
REGULATORY_HAIRCUTS = {
    CollateralAssetType.CASH: {
        "same_currency": 0.0,
        "other_currency": 0.08,
    },
    CollateralAssetType.GOVERNMENT_BOND: {
        "AAA_AA": {
            "0-1y": 0.005,
            "1-5y": 0.02,
            "5-10y": 0.04,
            ">10y": 0.06,
        },
        "A_BBB": {
            "0-1y": 0.01,
            "1-5y": 0.03,
            "5-10y": 0.06,
            ">10y": 0.12,
        },
    },
    CollateralAssetType.CORPORATE_BOND: {
        "AAA_AA": {
            "0-1y": 0.01,
            "1-5y": 0.04,
            "5-10y": 0.08,
            ">10y": 0.12,
        },
    },
    CollateralAssetType.EQUITY: {
        "main_index": 0.15,
        "other": 0.25,
    },
    CollateralAssetType.GOLD: 0.15,
}


@dataclass
class CollateralAsset:
    """Individual collateral asset."""
    asset_id: str = field(default_factory=lambda: f"COL-{uuid.uuid4().hex[:8].upper()}")
    asset_type: CollateralAssetType = CollateralAssetType.CASH
    currency: str = "USD"
    quantity: float = 0.0
    market_value: float = 0.0
    haircut: float = 0.0
    maturity: Optional[date] = None
    rating: str = "AAA"
    issuer: str = ""
    isin: str = ""
    
    def collateral_value(self) -> float:
        """Calculate post-haircut collateral value."""
        return self.market_value * (1 - self.haircut)
    
    def apply_regulatory_haircut(self) -> float:
        """Apply standard regulatory haircut."""
        if self.asset_type == CollateralAssetType.CASH:
            self.haircut = 0.0
        elif self.asset_type == CollateralAssetType.GOLD:
            self.haircut = 0.15
        elif self.asset_type == CollateralAssetType.EQUITY:
            self.haircut = 0.25
        elif self.asset_type in [CollateralAssetType.GOVERNMENT_BOND, 
                                  CollateralAssetType.CORPORATE_BOND]:
            # Simplified - use 4% default
            self.haircut = 0.04
        return self.haircut


@dataclass
class CollateralPool(ModelBase):
    """Pool of collateral assets."""
    pool_id: str = field(default_factory=lambda: f"POOL-{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    owner_id: str = ""
    assets: List[CollateralAsset] = field(default_factory=list)
    base_currency: str = "USD"
    
    def validate(self) -> bool:
        return True
    
    def total_market_value(self) -> float:
        """Total market value before haircuts."""
        return sum(a.market_value for a in self.assets)
    
    def total_collateral_value(self) -> float:
        """Total collateral value after haircuts."""
        return sum(a.collateral_value() for a in self.assets)
    
    def value_by_type(self) -> Dict[CollateralAssetType, float]:
        """Breakdown by asset type."""
        result = {}
        for asset in self.assets:
            if asset.asset_type not in result:
                result[asset.asset_type] = 0.0
            result[asset.asset_type] += asset.collateral_value()
        return result
    
    def add_asset(self, asset: CollateralAsset) -> None:
        """Add collateral asset."""
        self.assets.append(asset)
    
    def remove_asset(self, asset_id: str) -> bool:
        """Remove collateral asset."""
        for i, asset in enumerate(self.assets):
            if asset.asset_id == asset_id:
                self.assets.pop(i)
                return True
        return False


@dataclass
class MarginCall:
    """Margin call record."""
    call_id: str = field(default_factory=lambda: f"MC-{uuid.uuid4().hex[:8].upper()}")
    counterparty_id: str = ""
    netting_set_id: str = ""
    call_date: datetime = field(default_factory=datetime.now)
    call_type: str = "variation"  # variation, initial, regulatory
    call_amount: float = 0.0
    currency: str = "USD"
    due_date: date = field(default_factory=date.today)
    status: str = "pending"  # pending, received, disputed, settled
    
    # Calculation details
    exposure: float = 0.0
    existing_collateral: float = 0.0
    threshold: float = 0.0
    minimum_transfer_amount: float = 0.0
    
    def calculate_call_amount(self) -> float:
        """Calculate margin call amount."""
        uncollateralized = max(0, self.exposure - self.existing_collateral - self.threshold)
        if uncollateralized > self.minimum_transfer_amount:
            self.call_amount = uncollateralized
        else:
            self.call_amount = 0.0
        return self.call_amount


@dataclass
class CollateralMovement:
    """Record of collateral movement."""
    movement_id: str = field(default_factory=lambda: f"MOV-{uuid.uuid4().hex[:8].upper()}")
    movement_date: datetime = field(default_factory=datetime.now)
    from_party: str = ""
    to_party: str = ""
    asset: Optional[CollateralAsset] = None
    amount: float = 0.0
    currency: str = "USD"
    movement_type: str = "delivery"  # delivery, return, substitution
    related_margin_call: str = ""
    status: str = "pending"


@dataclass
class EligibilitySchedule:
    """Collateral eligibility schedule."""
    schedule_id: str = field(default_factory=lambda: f"ELIG-{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    
    # Eligible asset types
    eligible_cash_currencies: List[str] = field(default_factory=lambda: ["USD", "EUR", "GBP"])
    eligible_government_bonds: List[str] = field(default_factory=lambda: ["US", "DE", "GB", "FR", "JP"])
    eligible_corporate_bonds: bool = False
    min_corporate_rating: str = "A"
    eligible_equity: bool = False
    main_indices_only: bool = True
    eligible_gold: bool = False
    
    # Concentration limits
    max_single_issuer_pct: float = 0.10
    max_asset_class_pct: float = 0.50
    max_currency_mismatch_pct: float = 0.20
    
    def is_eligible(self, asset: CollateralAsset) -> bool:
        """Check if asset is eligible."""
        if asset.asset_type == CollateralAssetType.CASH:
            return asset.currency in self.eligible_cash_currencies
        elif asset.asset_type == CollateralAssetType.GOVERNMENT_BOND:
            return True  # Simplified
        elif asset.asset_type == CollateralAssetType.CORPORATE_BOND:
            return self.eligible_corporate_bonds
        elif asset.asset_type == CollateralAssetType.EQUITY:
            return self.eligible_equity
        elif asset.asset_type == CollateralAssetType.GOLD:
            return self.eligible_gold
        return False


__all__ = [
    "CollateralAssetType",
    "CollateralCurrency",
    "REGULATORY_HAIRCUTS",
    "CollateralAsset",
    "CollateralPool",
    "MarginCall",
    "CollateralMovement",
    "EligibilitySchedule",
]
