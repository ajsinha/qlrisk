"""
QLRisk - Portfolio Model v1.2.0
==============================================

Portfolio aggregation and management models.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Set
from enum import Enum
import uuid

from .trade import Trade
from .counterparty import NettingSet


class PortfolioType(Enum):
    """Portfolio type classification."""
    TRADING = "trading"
    BANKING = "banking"
    HEDGING = "hedging"
    INVESTMENT = "investment"


class AggregationLevel(Enum):
    """Aggregation level for exposure calculation."""
    TRADE = "trade"
    NETTING_SET = "netting_set"
    COUNTERPARTY = "counterparty"
    PORTFOLIO = "portfolio"
    ENTITY = "entity"




def _asset_class(trade) -> str:
    """Asset class of a trade: explicit attribute if present, else the trade type."""
    explicit = getattr(trade, "asset_class", None)
    if explicit:
        return getattr(explicit, "value", explicit)
    return getattr(trade.trade_type, "value", str(trade.trade_type))

@dataclass
class PortfolioSummary:
    """Summary statistics for a portfolio."""
    total_trades: int = 0
    total_notional: float = 0.0
    total_mtm: float = 0.0
    positive_mtm: float = 0.0
    negative_mtm: float = 0.0
    currencies: Set[str] = field(default_factory=set)
    asset_classes: Set[str] = field(default_factory=set)
    counterparties: Set[str] = field(default_factory=set)
    netting_sets: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_trades": self.total_trades,
            "total_notional": self.total_notional,
            "total_mtm": self.total_mtm,
            "positive_mtm": self.positive_mtm,
            "negative_mtm": self.negative_mtm,
            "currencies": list(self.currencies),
            "asset_classes": list(self.asset_classes),
            "counterparties": list(self.counterparties),
            "netting_sets": self.netting_sets,
        }


@dataclass
class Portfolio:
    """Portfolio of trades with aggregation capabilities."""
    portfolio_id: str = field(default_factory=lambda: f"PF-{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    portfolio_type: PortfolioType = PortfolioType.TRADING
    base_currency: str = "USD"
    owner_entity: str = ""
    trades: List[Trade] = field(default_factory=list)
    netting_sets: Dict[str, NettingSet] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> bool:
        return bool(self.portfolio_id)
    
    def add_trade(self, trade: Trade) -> None:
        """Add a trade to the portfolio."""
        self.trades.append(trade)
    
    def remove_trade(self, trade_id: str) -> bool:
        """Remove a trade by ID."""
        for i, trade in enumerate(self.trades):
            if trade.trade_id == trade_id:
                self.trades.pop(i)
                return True
        return False
    
    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """Get a trade by ID."""
        for trade in self.trades:
            if trade.trade_id == trade_id:
                return trade
        return None
    
    def get_trades_by_counterparty(self, counterparty_id: str) -> List[Trade]:
        """Get all trades for a counterparty."""
        return [t for t in self.trades if t.counterparty_id == counterparty_id]
    
    def get_trades_by_asset_class(self, asset_class: str) -> List[Trade]:
        """Get all trades for an asset class."""
        return [t for t in self.trades if _asset_class(t) == asset_class]
    
    def get_trades_by_currency(self, currency: str) -> List[Trade]:
        """Get all trades for a currency."""
        return [t for t in self.trades if t.currency == currency]
    
    def get_active_trades(self, as_of_date: date = None) -> List[Trade]:
        """Get trades that are active as of a date."""
        ref_date = as_of_date or date.today()
        return [t for t in self.trades 
                if t.effective_date <= ref_date <= t.maturity_date]
    
    def calculate_summary(self) -> PortfolioSummary:
        """Calculate portfolio summary statistics."""
        summary = PortfolioSummary()
        summary.total_trades = len(self.trades)
        
        for trade in self.trades:
            summary.total_notional += trade.notional
            mtm = getattr(trade, 'mtm', 0.0)
            summary.total_mtm += mtm
            
            if mtm > 0:
                summary.positive_mtm += mtm
            else:
                summary.negative_mtm += mtm
            
            summary.currencies.add(trade.currency)
            summary.asset_classes.add(_asset_class(trade))
            summary.counterparties.add(trade.counterparty_id)
        
        summary.netting_sets = len(self.netting_sets)
        
        return summary
    
    def group_by_netting_set(self) -> Dict[str, List[Trade]]:
        """Group trades by netting set."""
        groups: Dict[str, List[Trade]] = {}
        
        for trade in self.trades:
            ns_id = getattr(trade, 'netting_set_id', 'default')
            if ns_id not in groups:
                groups[ns_id] = []
            groups[ns_id].append(trade)
        
        return groups


@dataclass
class PortfolioSnapshot:
    """Point-in-time snapshot of a portfolio."""
    snapshot_id: str = field(default_factory=lambda: f"SNAP-{uuid.uuid4().hex[:8].upper()}")
    portfolio_id: str = ""
    snapshot_date: datetime = field(default_factory=datetime.now)
    summary: Optional[PortfolioSummary] = None
    exposures: Dict[str, float] = field(default_factory=dict)
    risk_metrics: Dict[str, float] = field(default_factory=dict)
    
    def validate(self) -> bool:
        return bool(self.snapshot_id)


__all__ = [
    "PortfolioType",
    "AggregationLevel", 
    "PortfolioSummary",
    "Portfolio",
    "PortfolioSnapshot",
]
