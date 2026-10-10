"""
Trade Model - Trade representation for QLRisk

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid

from .base import ModelBase
from ..core.exceptions import ValidationError
from ..core.validators import Validators


class TradeType(Enum):
    """Trade type enumeration."""
    INTEREST_RATE_SWAP = "IRS"
    FORWARD_RATE_AGREEMENT = "FRA"
    FX_FORWARD = "FX_FWD"
    FX_OPTION = "FX_OPT"
    CREDIT_DEFAULT_SWAP = "CDS"
    EQUITY_OPTION = "EQ_OPT"
    EQUITY_FORWARD = "EQ_FWD"
    COMMODITY_FORWARD = "CMD_FWD"
    COMMODITY_OPTION = "CMD_OPT"
    REPO = "REPO"
    SECURITIES_LENDING = "SEC_LEND"


class TradeStatus(Enum):
    """Trade status enumeration."""
    PENDING = "pending"
    ACTIVE = "active"
    MATURED = "matured"
    TERMINATED = "terminated"
    DEFAULTED = "defaulted"


class TradeDirection(Enum):
    """Trade direction enumeration."""
    BUY = "buy"
    SELL = "sell"
    PAY = "pay"
    RECEIVE = "receive"


@dataclass
class Trade(ModelBase):
    """
    Trade model representing a financial transaction.
    """
    trade_id: str = field(default_factory=lambda: f"TRD-{uuid.uuid4().hex[:8].upper()}")
    trade_type: TradeType = TradeType.INTEREST_RATE_SWAP
    status: TradeStatus = TradeStatus.ACTIVE
    direction: TradeDirection = TradeDirection.BUY
    
    # Counterparty information
    counterparty_id: str = ""
    netting_set_id: Optional[str] = None
    
    # Trade economics
    notional: float = 0.0
    currency: str = "USD"
    trade_date: date = field(default_factory=date.today)
    effective_date: date = field(default_factory=date.today)
    maturity_date: date = field(default_factory=date.today)
    
    # Pricing information
    mark_to_market: float = 0.0
    initial_margin: float = 0.0
    variation_margin: float = 0.0
    
    # Product-specific attributes
    product_attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Risk metrics (calculated)
    current_exposure: float = 0.0
    potential_future_exposure: float = 0.0
    expected_exposure: float = 0.0
    
    def validate(self) -> bool:
        """Validate trade data."""
        True
        True
        True
        
        if self.notional < 0:
            raise ValueError(
                "Notional cannot be negative",
                field="notional",
                actual=self.notional
            )
        
        if self.maturity_date < self.effective_date:
            raise ValueError(
                "Maturity date must be after effective date",
                field="maturity_date",
                expected=f"> {self.effective_date}",
                actual=self.maturity_date
            )
        
        return True

    def is_active(self) -> bool:
        """Check if trade is active."""
        return self.status == TradeStatus.ACTIVE

    def is_matured(self) -> bool:
        """Check if trade has matured."""
        return date.today() >= self.maturity_date

    def time_to_maturity(self, from_date: Optional[date] = None) -> float:
        """
        Calculate time to maturity in years.

        Args:
            from_date: Reference date (default: today)

        Returns:
            Time to maturity in years
        """
        ref_date = from_date or date.today()
        days = (self.maturity_date - ref_date).days
        return max(days / 365.0, 0.0)

    def get_exposure(self) -> float:
        """
        Get current exposure (max of MTM and 0).

        Returns:
            Current exposure
        """
        return max(self.mark_to_market, 0.0)

    def get_net_exposure(self, collateral: float = 0.0) -> float:
        """
        Get net exposure after collateral.

        Args:
            collateral: Collateral amount

        Returns:
            Net exposure
        """
        return max(self.mark_to_market - collateral, 0.0)


@dataclass
class TradePortfolio(ModelBase):
    """
    Collection of trades for a counterparty or netting set.
    """
    portfolio_id: str = field(default_factory=lambda: f"PF-{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    trades: List[Trade] = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate portfolio."""
        return True

    def add_trade(self, trade: Trade):
        """Add trade to portfolio."""
        self.trades.append(trade)
        self.updated_at = datetime.now()

    def remove_trade(self, trade_id: str) -> Optional[Trade]:
        """Remove trade from portfolio."""
        for i, trade in enumerate(self.trades):
            if trade.trade_id == trade_id:
                return self.trades.pop(i)
        return None

    def get_active_trades(self) -> List[Trade]:
        """Get all active trades."""
        return [t for t in self.trades if t.is_active()]

    def total_notional(self, currency: Optional[str] = None) -> float:
        """
        Calculate total notional.

        Args:
            currency: Optional currency filter

        Returns:
            Total notional
        """
        trades = self.trades
        if currency:
            trades = [t for t in trades if t.currency == currency]
        return sum(t.notional for t in trades)

    def total_mtm(self) -> float:
        """Calculate total mark-to-market."""
        return sum(t.mark_to_market for t in self.trades)

    def total_exposure(self) -> float:
        """Calculate total exposure."""
        return sum(t.get_exposure() for t in self.trades)

    def net_exposure(self) -> float:
        """Calculate net exposure (for netting sets)."""
        total_mtm = self.total_mtm()
        return max(total_mtm, 0.0)

    def by_trade_type(self, trade_type: TradeType) -> List[Trade]:
        """Get trades by type."""
        return [t for t in self.trades if t.trade_type == trade_type]

    def by_currency(self, currency: str) -> List[Trade]:
        """Get trades by currency."""
        return [t for t in self.trades if t.currency == currency]

    def by_counterparty(self, counterparty_id: str) -> List[Trade]:
        """Get trades by counterparty."""
        return [t for t in self.trades if t.counterparty_id == counterparty_id]

    def __len__(self) -> int:
        return len(self.trades)

    def __iter__(self):
        return iter(self.trades)
