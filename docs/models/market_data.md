# Market Data Model Documentation v1.2.0

## Overview

The Market Data module provides models for market data snapshots, quotes, and real-time market information.

## Classes

### QuoteType (Enum)

Types of market quotes.

| Value | Name | Description |
|-------|------|-------------|
| `bid` | `BID` | Bid price |
| `ask` | `ASK` | Ask price |
| `mid` | `MID` | Mid price |
| `last` | `LAST` | Last traded |
| `close` | `CLOSE` | Close price |

### Quote (Dataclass)

Single market quote.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | str | required | Instrument symbol |
| `quote_type` | QuoteType | QuoteType.MID | Quote type |
| `value` | float | 0.0 | Quote value |
| `currency` | str | 'USD' | Quote currency |
| `timestamp` | datetime | now() | Quote timestamp |
| `source` | str | 'market' | Data source |
| `metadata` | Dict | dict() |  |

### MarketDataSnapshot (Dataclass)

Point-in-time market data snapshot.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | str | auto-generated |  |
| `created_at` | datetime | now() |  |
| `updated_at` | datetime | now() |  |
| `metadata` | Dict | dict() |  |
| `snapshot_date` | date | today() | Snapshot timestamp |
| `snapshot_time` | datetime | now() |  |
| `quotes` | Dict | dict() | Symbol → Quote |
| `fx_rates` | Dict | dict() | Pair → Rate |
| `equity_prices` | Dict | dict() | Symbol → Price |
| `yield_curves` | Dict | dict() | Currency → Curve |
| `credit_curves` | Dict | dict() | Entity → Curve |
| `volatility_surfaces` | Dict | dict() |  |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_quote(symbol)` | Quote | Get quote by symbol |
| `get_fx_rate(base, quote)` | float | Get FX rate (inverts if only the reverse pair is stored) |
| `get_yield_curve(ccy)` | YieldCurve | Get yield curve |
| `get_credit_curve(entity)` | CreditCurve | Get credit curve |

### MarketData (Dataclass)

Real-time market data container.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | str | auto-generated |  |
| `created_at` | datetime | now() |  |
| `updated_at` | datetime | now() |  |
| `metadata` | Dict | dict() |  |
| `market_data_id` | str | '' |  |
| `current_snapshot` | Union | None |  |
| `historical_snapshots` | Dict | dict() |  |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_latest_snapshot()` | MarketDataSnapshot | Most recent snapshot |
| `add_snapshot(snapshot)` | None | Add snapshot |
| `update_quote(quote)` | None | Update live quote |

## Usage Examples

```python
from qlrisk.models import MarketData, MarketDataSnapshot, Quote, YieldCurve
from qlrisk.models.market_data import QuoteType
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
eur_rate = snapshot.get_fx_rate("EUR", "USD")
aapl_price = snapshot.equity_prices.get("AAPL")
```

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
