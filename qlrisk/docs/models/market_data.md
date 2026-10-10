# Market Data Model Documentation v1.2.0

## Overview

The Market Data module provides models for market data snapshots, quotes, and real-time market information.

## Classes

### QuoteType (Enum)

Types of market quotes.

| Value | Description |
|-------|-------------|
| `BID` | Bid price |
| `ASK` | Ask price |
| `MID` | Mid price |
| `LAST` | Last traded |
| `CLOSE` | Close price |
| `OPEN` | Open price |
| `HIGH` | High price |
| `LOW` | Low price |

### Quote (Dataclass)

Single market quote.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | str | "" | Instrument symbol |
| `quote_type` | QuoteType | MID | Quote type |
| `value` | float | 0.0 | Quote value |
| `currency` | str | "USD" | Quote currency |
| `timestamp` | datetime | now | Quote timestamp |
| `source` | str | "" | Data source |

### MarketDataSnapshot (Dataclass)

Point-in-time market data snapshot.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `snapshot_id` | str | Auto-generated | Unique identifier |
| `snapshot_date` | datetime | now | Snapshot timestamp |
| `quotes` | Dict[str, Quote] | {} | Symbol → Quote |
| `yield_curves` | Dict[str, YieldCurve] | {} | Currency → Curve |
| `credit_curves` | Dict[str, CreditCurve] | {} | Entity → Curve |
| `vol_surfaces` | Dict[str, VolSurface] | {} | Underlying → Surface |
| `fx_rates` | Dict[str, float] | {} | Pair → Rate |
| `equity_prices` | Dict[str, float] | {} | Symbol → Price |
| `commodity_prices` | Dict[str, float] | {} | Symbol → Price |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_quote(symbol)` | Quote | Get quote by symbol |
| `get_fx_rate(pair)` | float | Get FX rate |
| `get_yield_curve(ccy)` | YieldCurve | Get yield curve |
| `get_credit_curve(entity)` | CreditCurve | Get credit curve |

### MarketData (Dataclass)

Real-time market data container.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_id` | str | Auto-generated | Unique identifier |
| `as_of_date` | date | today | Valuation date |
| `snapshots` | List[MarketDataSnapshot] | [] | Historical snapshots |
| `live_quotes` | Dict[str, Quote] | {} | Live quotes |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_latest_snapshot()` | MarketDataSnapshot | Most recent snapshot |
| `add_snapshot(snapshot)` | None | Add snapshot |
| `update_quote(quote)` | None | Update live quote |

## Usage Examples

```python
from models import (
    MarketData, MarketDataSnapshot, Quote, QuoteType,
    YieldCurve
)
from datetime import datetime

# Create quotes
fx_quote = Quote(
    symbol="EURUSD",
    quote_type=QuoteType.MID,
    value=1.0850,
    currency="USD",
    source="Reuters"
)

equity_quote = Quote(
    symbol="AAPL",
    quote_type=QuoteType.LAST,
    value=178.50,
    currency="USD"
)

# Create snapshot
snapshot = MarketDataSnapshot(
    snapshot_date=datetime.now(),
    fx_rates={"EURUSD": 1.0850, "GBPUSD": 1.2650},
    equity_prices={"AAPL": 178.50, "MSFT": 375.20}
)
snapshot.quotes["EURUSD"] = fx_quote

# Get data
eur_rate = snapshot.get_fx_rate("EURUSD")
aapl_price = snapshot.equity_prices.get("AAPL")
```

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
