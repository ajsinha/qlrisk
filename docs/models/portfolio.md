# Portfolio Model Documentation v1.2.0

## Overview

The Portfolio model provides aggregation and management capabilities for collections of trades, supporting various risk aggregation levels and netting set grouping.

## Classes

### PortfolioType (Enum)

Portfolio classification.

| Value | Description |
|-------|-------------|
| `TRADING` | Trading book |
| `BANKING` | Banking book |
| `HEDGING` | Hedging portfolio |
| `INVESTMENT` | Investment portfolio |

### AggregationLevel (Enum)

Aggregation hierarchy for exposure calculation.

| Value | Description |
|-------|-------------|
| `TRADE` | Individual trade level |
| `NETTING_SET` | Netting set level |
| `COUNTERPARTY` | Counterparty level |
| `PORTFOLIO` | Portfolio level |
| `ENTITY` | Legal entity level |

### PortfolioSummary (Dataclass)

Summary statistics for a portfolio.

| Attribute | Type | Description |
|-----------|------|-------------|
| `total_trades` | int | Number of trades |
| `total_notional` | float | Sum of notionals |
| `total_mtm` | float | Net MTM |
| `positive_mtm` | float | Sum of positive MTMs |
| `negative_mtm` | float | Sum of negative MTMs |
| `currencies` | Set[str] | Unique currencies |
| `asset_classes` | Set[str] | Unique asset classes |
| `counterparties` | Set[str] | Unique counterparties |
| `netting_sets` | int | Number of netting sets |

### Portfolio (Dataclass)

Main portfolio container.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `portfolio_id` | str | Auto-generated | Unique identifier |
| `name` | str | "" | Portfolio name |
| `portfolio_type` | PortfolioType | TRADING | Classification |
| `base_currency` | str | "USD" | Base currency |
| `owner_entity` | str | "" | Owning entity |
| `trades` | List[Trade] | [] | Trade collection |
| `netting_sets` | Dict | {} | Netting set mappings |

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

| Attribute | Type | Description |
|-----------|------|-------------|
| `snapshot_id` | str | Unique identifier |
| `portfolio_id` | str | Source portfolio |
| `snapshot_date` | datetime | Snapshot timestamp |
| `summary` | PortfolioSummary | Summary at snapshot |
| `exposures` | Dict[str, float] | Exposure metrics |
| `risk_metrics` | Dict[str, float] | Risk metrics |

## Usage Examples

```python
from models import Portfolio, PortfolioType, Trade
from datetime import date

# Create portfolio
portfolio = Portfolio(
    name="Trading Book Alpha",
    portfolio_type=PortfolioType.TRADING,
    base_currency="USD"
)

# Add trades
trade1 = Trade(product_type="IRS", notional=10e6, counterparty_id="CP-001")
trade2 = Trade(product_type="FXF", notional=5e6, counterparty_id="CP-002")

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
