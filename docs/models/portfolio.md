# Portfolio Model Documentation v1.2.0

## Overview

The Portfolio model provides aggregation and management capabilities for collections of trades, supporting various risk aggregation levels and netting set grouping.

## Classes

### PortfolioType (Enum)

Portfolio classification.

| Value | Name | Description |
|-------|------|-------------|
| `trading` | `TRADING` | Trading book |
| `banking` | `BANKING` | Banking book |
| `hedging` | `HEDGING` | Hedging portfolio |
| `investment` | `INVESTMENT` | Investment portfolio |

### AggregationLevel (Enum)

Aggregation hierarchy for exposure calculation.

| Value | Name | Description |
|-------|------|-------------|
| `trade` | `TRADE` | Individual trade level |
| `netting_set` | `NETTING_SET` | Netting set level |
| `counterparty` | `COUNTERPARTY` | Counterparty level |
| `portfolio` | `PORTFOLIO` | Portfolio level |
| `entity` | `ENTITY` | Legal entity level |

### PortfolioSummary (Dataclass)

Summary statistics for a portfolio.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `total_trades` | int | 0 | Number of trades |
| `total_notional` | float | 0.0 | Sum of notionals |
| `total_mtm` | float | 0.0 | Net MTM |
| `positive_mtm` | float | 0.0 | Sum of positive MTMs |
| `negative_mtm` | float | 0.0 | Sum of negative MTMs |
| `currencies` | Set | set() | Unique currencies |
| `asset_classes` | Set | set() | Unique asset classes |
| `counterparties` | Set | set() | Unique counterparties |
| `netting_sets` | int | 0 | Number of netting sets |

### Portfolio (Dataclass)

Main portfolio container.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `portfolio_id` | str | auto-generated | Unique identifier |
| `name` | str | '' | Portfolio name |
| `portfolio_type` | PortfolioType | PortfolioType.TRADING | Classification |
| `base_currency` | str | 'USD' | Base currency |
| `owner_entity` | str | '' | Owning entity |
| `trades` | List | list() | Trade collection |
| `netting_sets` | Dict | dict() | Netting set mappings |
| `created_at` | datetime | now() |  |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `add_trade(trade)` | None | Add trade to portfolio |
| `remove_trade(trade_id)` | bool | Remove trade by ID |
| `get_trade(trade_id)` | Trade | Get trade by ID |
| `get_trades_by_counterparty(cp_id)` | List[Trade] | Filter by counterparty |
| `get_trades_by_asset_class(ac)` | List[Trade] | Filter by asset class |
| `get_trades_by_currency(ccy)` | List[Trade] | Filter by currency |
| `get_active_trades(as_of)` | List[Trade] | Get active trades |
| `calculate_summary()` | PortfolioSummary | Calculate statistics |
| `group_by_netting_set()` | Dict | Group trades by NS |

### PortfolioSnapshot (Dataclass)

Point-in-time portfolio state.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `snapshot_id` | str | auto-generated | Unique identifier |
| `portfolio_id` | str | '' | Source portfolio |
| `snapshot_date` | datetime | now() | Snapshot timestamp |
| `summary` | Union | None | Summary at snapshot |
| `exposures` | Dict | dict() | Exposure metrics |
| `risk_metrics` | Dict | dict() | Risk metrics |

## Usage Examples

```python
from qlrisk.models import Portfolio, PortfolioType, Trade, TradeType
from datetime import date

# Create portfolio
portfolio = Portfolio(
    portfolio_id="PF-ALPHA",
    name="Trading Book Alpha",
    portfolio_type=PortfolioType.TRADING,
    base_currency="USD"
)

# Add trades
trade1 = Trade(trade_id="T1", trade_type=TradeType.INTEREST_RATE_SWAP, notional=10e6, counterparty_id="CP-001")
trade2 = Trade(trade_id="T2", trade_type=TradeType.FX_FORWARD, notional=5e6, counterparty_id="CP-002")

portfolio.add_trade(trade1)
portfolio.add_trade(trade2)

# Calculate summary
summary = portfolio.calculate_summary()
print(f"Total trades: {summary.total_trades}")
print(f"Total notional: ${summary.total_notional:,.0f}")

# Group by counterparty
cp_trades = portfolio.get_trades_by_counterparty("CP-001")
```

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
