# Trade Model Documentation v1.2.0

## Overview

The Trade model represents individual financial transactions in QLRisk. It captures all essential attributes needed for market risk and counterparty credit risk calculations.

## Classes

### TradeType (Enum)

Enumeration of trade types.

| Value | Description |
|-------|-------------|
| `BUY` | Buy/Long position |
| `SELL` | Sell/Short position |
| `PAY` | Pay fixed (swaps) |
| `RECEIVE` | Receive fixed (swaps) |

### TradeStatus (Enum)

Trade lifecycle status.

| Value | Description |
|-------|-------------|
| `PENDING` | Trade not yet active |
| `ACTIVE` | Trade is live |
| `MATURED` | Trade has matured |
| `TERMINATED` | Trade terminated early |
| `DEFAULTED` | Counterparty defaulted |

### Trade (Dataclass)

Main trade representation.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `trade_id` | str | Auto-generated | Unique trade identifier |
| `product_type` | str | "" | Type of financial product |
| `asset_class` | str | "" | Asset class (IR, FX, Credit, etc.) |
| `notional` | float | 0.0 | Notional/principal amount |
| `currency` | str | "USD" | Trade currency |
| `effective_date` | date | today | Start date |
| `maturity_date` | date | today | End date |
| `counterparty_id` | str | "" | Counterparty identifier |
| `netting_set_id` | str | "" | Netting set for aggregation |
| `trade_type` | TradeType | BUY | Direction of trade |
| `status` | TradeStatus | ACTIVE | Current status |
| `mtm` | float | 0.0 | Mark-to-market value |
| `created_at` | datetime | now | Creation timestamp |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `validate()` | bool | Validate trade attributes |
| `time_to_maturity(from_date)` | float | Years to maturity |
| `is_active(as_of)` | bool | Check if active on date |

## Usage Examples

```python
from models import Trade, TradeType, TradeStatus
from datetime import date

# Create a trade
trade = Trade(
    product_type="IRS",
    asset_class="interest_rate",
    notional=10_000_000,
    currency="USD",
    effective_date=date(2024, 1, 1),
    maturity_date=date(2029, 1, 1),
    counterparty_id="CP-001",
    netting_set_id="NS-001",
    trade_type=TradeType.PAY,
    mtm=125000.0
)

# Check time to maturity
ttm = trade.time_to_maturity()
print(f"Time to maturity: {ttm:.2f} years")

# Validate
trade.validate()
```

## Related Models

- `Portfolio` - Collection of trades
- `NettingSet` - Netting agreement grouping
- `Counterparty` - Trade counterparty

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
