"""
Market Data Models - Market data representation for QLRisk

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

from .base import ModelBase
from .curve import YieldCurve, CreditCurve, VolatilitySurface
# from ..core.exceptions import DataError  # Removed - self-contained


class QuoteType(Enum):
    """Quote type enumeration."""
    BID = "bid"
    ASK = "ask"
    MID = "mid"
    LAST = "last"
    CLOSE = "close"


class AssetClass(Enum):
    """Asset class enumeration."""
    EQUITY = "equity"
    FX = "fx"
    RATES = "rates"
    CREDIT = "credit"
    COMMODITY = "commodity"


@dataclass
class Quote:
    """
    Market quote representation.
    """
    symbol: str
    quote_type: QuoteType = QuoteType.MID
    value: float = 0.0
    currency: str = "USD"
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "market"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def spread(self, bid: float, ask: float) -> float:
        """Calculate bid-ask spread."""
        return ask - bid

    def mid(self, bid: float, ask: float) -> float:
        """Calculate mid price."""
        return (bid + ask) / 2


@dataclass
class FXRate:
    """Foreign exchange rate."""
    base_currency: str = "USD"
    quote_currency: str = "EUR"
    rate: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)

    def invert(self) -> 'FXRate':
        """Get inverted rate."""
        return FXRate(
            base_currency=self.quote_currency,
            quote_currency=self.base_currency,
            rate=1.0 / self.rate if self.rate != 0 else 0.0,
            timestamp=self.timestamp
        )

    def convert(self, amount: float, from_currency: str) -> float:
        """
        Convert amount between currencies.

        Args:
            amount: Amount to convert
            from_currency: Source currency

        Returns:
            Converted amount
        """
        if from_currency == self.base_currency:
            return amount * self.rate
        elif from_currency == self.quote_currency:
            return amount / self.rate if self.rate != 0 else 0.0
        else:
            raise ValueError(f"Currency {from_currency} not in rate pair")


@dataclass
class EquityPrice:
    """Equity price data."""
    symbol: str = ""
    price: float = 0.0
    currency: str = "USD"
    dividend_yield: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketDataSnapshot(ModelBase):
    """
    Snapshot of market data at a point in time.
    """
    snapshot_date: date = field(default_factory=date.today)
    snapshot_time: datetime = field(default_factory=datetime.now)
    
    # Quotes
    quotes: Dict[str, Quote] = field(default_factory=dict)
    
    # FX rates
    fx_rates: Dict[str, FXRate] = field(default_factory=dict)
    
    # Equity prices
    equity_prices: Dict[str, EquityPrice] = field(default_factory=dict)
    
    # Curves
    yield_curves: Dict[str, YieldCurve] = field(default_factory=dict)
    credit_curves: Dict[str, CreditCurve] = field(default_factory=dict)
    volatility_surfaces: Dict[str, VolatilitySurface] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate snapshot."""
        return True

    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get quote by symbol."""
        return self.quotes.get(symbol)

    def get_fx_rate(
        self,
        base_currency: str,
        quote_currency: str
    ) -> Optional[float]:
        """
        Get FX rate.

        Args:
            base_currency: Base currency
            quote_currency: Quote currency

        Returns:
            Exchange rate
        """
        key = f"{base_currency}/{quote_currency}"
        if key in self.fx_rates:
            return self.fx_rates[key].rate
        
        # Try inverse
        inverse_key = f"{quote_currency}/{base_currency}"
        if inverse_key in self.fx_rates:
            rate = self.fx_rates[inverse_key].rate
            return 1.0 / rate if rate != 0 else None
        
        return None

    def get_yield_curve(self, currency: str) -> Optional[YieldCurve]:
        """Get yield curve by currency."""
        return self.yield_curves.get(currency)

    def get_credit_curve(self, entity_id: str) -> Optional[CreditCurve]:
        """Get credit curve by entity ID."""
        return self.credit_curves.get(entity_id)

    def get_volatility_surface(self, underlying: str) -> Optional[VolatilitySurface]:
        """Get volatility surface by underlying."""
        return self.volatility_surfaces.get(underlying)

    def add_quote(self, quote: Quote):
        """Add or update quote."""
        self.quotes[quote.symbol] = quote

    def add_fx_rate(self, fx_rate: FXRate):
        """Add or update FX rate."""
        key = f"{fx_rate.base_currency}/{fx_rate.quote_currency}"
        self.fx_rates[key] = fx_rate

    def add_yield_curve(self, curve: YieldCurve):
        """Add or update yield curve."""
        self.yield_curves[curve.currency] = curve

    def add_credit_curve(self, curve: CreditCurve):
        """Add or update credit curve."""
        self.credit_curves[curve.curve_id] = curve

    def add_volatility_surface(self, surface: VolatilitySurface):
        """Add or update volatility surface."""
        self.volatility_surfaces[surface.underlying] = surface


@dataclass
class MarketData(ModelBase):
    """
    Market data container with historical snapshots.
    """
    market_data_id: str = ""
    
    # Current snapshot
    current_snapshot: Optional[MarketDataSnapshot] = None
    
    # Historical snapshots
    historical_snapshots: Dict[date, MarketDataSnapshot] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate market data."""
        return True

    def get_snapshot(self, as_of_date: Optional[date] = None) -> Optional[MarketDataSnapshot]:
        """
        Get snapshot for a date.

        Args:
            as_of_date: Date for snapshot (None for current)

        Returns:
            Market data snapshot
        """
        if as_of_date is None:
            return self.current_snapshot
        return self.historical_snapshots.get(as_of_date)

    def set_current_snapshot(self, snapshot: MarketDataSnapshot):
        """Set current snapshot."""
        self.current_snapshot = snapshot

    def add_historical_snapshot(self, snapshot: MarketDataSnapshot):
        """Add historical snapshot."""
        self.historical_snapshots[snapshot.snapshot_date] = snapshot

    def get_historical_dates(self) -> List[date]:
        """Get list of available historical dates."""
        return sorted(self.historical_snapshots.keys())

    def get_time_series(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Tuple[date, float]]:
        """
        Get time series of quote values.

        Args:
            symbol: Quote symbol
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            List of (date, value) tuples
        """
        result = []
        
        for dt, snapshot in sorted(self.historical_snapshots.items()):
            if start_date and dt < start_date:
                continue
            if end_date and dt > end_date:
                continue
            
            quote = snapshot.get_quote(symbol)
            if quote:
                result.append((dt, quote.value))
        
        return result
