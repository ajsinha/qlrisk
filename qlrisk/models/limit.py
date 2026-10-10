"""
QLRisk - Limit Model v1.2.0
==========================================

Credit and exposure limit management models.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid

from .base import ModelBase


class LimitType(Enum):
    """Type of limit."""
    CREDIT = "credit"
    EXPOSURE = "exposure"
    SETTLEMENT = "settlement"
    COUNTRY = "country"
    SECTOR = "sector"
    PRODUCT = "product"
    TENOR = "tenor"
    NOTIONAL = "notional"
    # Market risk
    VAR = "var"
    EXPECTED_SHORTFALL = "expected_shortfall"
    STRESSED_VAR = "stressed_var"
    STRESS_LOSS = "stress_loss"
    DV01 = "dv01"
    CS01 = "cs01"
    DELTA = "delta"
    VEGA = "vega"
    CAPITAL = "capital"


class LimitStatus(Enum):
    """Limit utilization status."""
    GREEN = "green"      # < 75%
    AMBER = "amber"      # 75-90%
    RED = "red"          # 90-100%
    BREACH = "breach"    # > 100%


class LimitAction(Enum):
    """Action on limit breach."""
    WARN = "warn"
    BLOCK = "block"
    ESCALATE = "escalate"
    APPROVE = "approve"


@dataclass
class Limit(ModelBase):
    """Credit or exposure limit."""
    limit_id: str = field(default_factory=lambda: f"LIM-{uuid.uuid4().hex[:8].upper()}")
    limit_type: LimitType = LimitType.CREDIT
    name: str = ""
    description: str = ""
    
    # Limit parameters
    limit_amount: float = 0.0
    currency: str = "USD"
    utilized_amount: float = 0.0
    available_amount: float = 0.0
    
    # Applicability
    counterparty_id: str = ""
    country_code: str = ""
    sector: str = ""
    product_type: str = ""
    
    # Validity
    effective_date: date = field(default_factory=date.today)
    expiry_date: Optional[date] = None
    
    # Thresholds
    warning_threshold: float = 0.75
    escalation_threshold: float = 0.90
    
    # Breach handling
    breach_action: LimitAction = LimitAction.WARN
    requires_approval: bool = False
    approved_by: str = ""
    
    def validate(self) -> bool:
        return self.limit_amount > 0
    
    def utilization_pct(self) -> float:
        """Calculate utilization percentage."""
        if self.limit_amount == 0:
            return 0.0
        return self.utilized_amount / self.limit_amount
    
    def status(self) -> LimitStatus:
        """Get current limit status."""
        util = self.utilization_pct()
        if util > 1.0:
            return LimitStatus.BREACH
        elif util > self.escalation_threshold:
            return LimitStatus.RED
        elif util > self.warning_threshold:
            return LimitStatus.AMBER
        else:
            return LimitStatus.GREEN
    
    def update_utilization(self, amount: float) -> bool:
        """Update limit utilization."""
        self.utilized_amount = amount
        self.available_amount = max(0, self.limit_amount - amount)
        return self.status() != LimitStatus.BREACH
    
    def can_allocate(self, additional_amount: float) -> bool:
        """Check if additional amount can be allocated."""
        new_total = self.utilized_amount + additional_amount
        return new_total <= self.limit_amount
    
    def is_active(self, as_of: date = None) -> bool:
        """Check if limit is currently active."""
        ref_date = as_of or date.today()
        if ref_date < self.effective_date:
            return False
        if self.expiry_date and ref_date > self.expiry_date:
            return False
        return True


@dataclass
class LimitHierarchy(ModelBase):
    """Hierarchical limit structure."""
    hierarchy_id: str = field(default_factory=lambda: f"HIER-{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    
    # Hierarchy levels
    entity_limit: Optional[Limit] = None
    country_limits: Dict[str, Limit] = field(default_factory=dict)
    sector_limits: Dict[str, Limit] = field(default_factory=dict)
    counterparty_limits: Dict[str, Limit] = field(default_factory=dict)
    
    def validate(self) -> bool:
        return True
    
    def check_all_limits(self, 
                         counterparty_id: str,
                         country: str,
                         sector: str,
                         amount: float) -> Dict[str, bool]:
        """Check all applicable limits."""
        results = {}
        
        if self.entity_limit:
            results["entity"] = self.entity_limit.can_allocate(amount)
        
        if country in self.country_limits:
            results["country"] = self.country_limits[country].can_allocate(amount)
        
        if sector in self.sector_limits:
            results["sector"] = self.sector_limits[sector].can_allocate(amount)
        
        if counterparty_id in self.counterparty_limits:
            results["counterparty"] = self.counterparty_limits[counterparty_id].can_allocate(amount)
        
        return results
    
    def all_limits_ok(self, **kwargs) -> bool:
        """Check if all limits pass."""
        results = self.check_all_limits(**kwargs)
        return all(results.values())


@dataclass
class LimitBreach:
    """Record of a limit breach."""
    breach_id: str = field(default_factory=lambda: f"BRE-{uuid.uuid4().hex[:8].upper()}")
    limit_id: str = ""
    breach_date: datetime = field(default_factory=datetime.now)
    breach_amount: float = 0.0
    utilized_at_breach: float = 0.0
    limit_amount: float = 0.0
    breach_pct: float = 0.0
    
    # Resolution
    resolution_status: str = "open"  # open, approved, remediated, closed
    resolution_date: Optional[datetime] = None
    resolution_notes: str = ""
    approved_by: str = ""
    
    def calculate_breach_pct(self) -> float:
        """Calculate breach percentage over limit."""
        if self.limit_amount == 0:
            return 0.0
        self.breach_pct = (self.utilized_at_breach / self.limit_amount) - 1.0
        return self.breach_pct


@dataclass
class LimitUtilizationHistory:
    """Historical limit utilization."""
    limit_id: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_snapshot(self, as_of: datetime, utilized: float, limit: float) -> None:
        """Add utilization snapshot."""
        self.history.append({
            "as_of": as_of,
            "utilized": utilized,
            "limit": limit,
            "utilization_pct": utilized / limit if limit > 0 else 0.0,
        })
    
    def peak_utilization(self) -> float:
        """Get peak historical utilization."""
        if not self.history:
            return 0.0
        return max(h["utilization_pct"] for h in self.history)
    
    def average_utilization(self) -> float:
        """Get average historical utilization."""
        if not self.history:
            return 0.0
        return sum(h["utilization_pct"] for h in self.history) / len(self.history)


__all__ = [
    "LimitType",
    "LimitStatus", 
    "LimitAction",
    "Limit",
    "LimitHierarchy",
    "LimitBreach",
    "LimitUtilizationHistory",
]
