# Trade Model Documentation
## Overview

The Trade model represents individual financial transactions in QLRisk. It captures all essential attributes needed for market risk and counterparty credit risk calculations.

## Classes

### TradeType (Enum)

Enumeration of trade types.

| Value | Name | Description |
|-------|------|-------------|
| `IRS` | `INTEREST_RATE_SWAP` |  |
| `FRA` | `FORWARD_RATE_AGREEMENT` |  |
| `FX_FWD` | `FX_FORWARD` |  |
| `FX_OPT` | `FX_OPTION` |  |
| `CDS` | `CREDIT_DEFAULT_SWAP` |  |
| `EQ_OPT` | `EQUITY_OPTION` |  |
| `EQ_FWD` | `EQUITY_FORWARD` |  |
| `CMD_FWD` | `COMMODITY_FORWARD` |  |
| `CMD_OPT` | `COMMODITY_OPTION` |  |
| `REPO` | `REPO` |  |
| `SEC_LEND` | `SECURITIES_LENDING` |  |

### TradeStatus (Enum)

Trade lifecycle status.

| Value | Name | Description |
|-------|------|-------------|
| `pending` | `PENDING` | Trade not yet active |
| `active` | `ACTIVE` | Trade is live |
| `matured` | `MATURED` | Trade has matured |
| `terminated` | `TERMINATED` | Trade terminated early |
| `defaulted` | `DEFAULTED` | Counterparty defaulted |

### Trade (Dataclass)

Main trade representation.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | str | auto-generated |  |
| `created_at` | datetime | now() | Creation timestamp |
| `updated_at` | datetime | now() |  |
| `metadata` | Dict | dict() |  |
| `trade_id` | str | auto-generated | Unique trade identifier |
| `trade_type` | TradeType | TradeType.INTEREST_RATE_SWAP | Direction of trade |
| `status` | TradeStatus | TradeStatus.ACTIVE | Current status |
| `direction` | TradeDirection | TradeDirection.BUY |  |
| `counterparty_id` | str | '' | Counterparty identifier |
| `netting_set_id` | Union | None | Netting set for aggregation |
| `notional` | float | 0.0 | Notional/principal amount |
| `currency` | str | 'USD' | Trade currency |
| `trade_date` | date | today() |  |
| `effective_date` | date | today() | Start date |
| `maturity_date` | date | today() | End date |
| `mark_to_market` | float | 0.0 |  |
| `initial_margin` | float | 0.0 |  |
| `variation_margin` | float | 0.0 |  |
| `product_attributes` | Dict | dict() |  |
| `current_exposure` | float | 0.0 |  |
| `potential_future_exposure` | float | 0.0 |  |
| `expected_exposure` | float | 0.0 |  |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `validate()` | bool | Validate trade attributes |
| `time_to_maturity(from_date)` | float | Years to maturity |
| `is_active(as_of)` | bool | Check if active on date |

## Usage Examples

```python
from qlrisk.models import Trade, TradeType, TradeStatus
from datetime import date

# Create a trade
trade = Trade(
    trade_id="IRS-001",
    trade_type=TradeType.INTEREST_RATE_SWAP,
    status=TradeStatus.ACTIVE,
    notional=10_000_000,
    currency="USD",
    effective_date=date(2024, 1, 1),
    maturity_date=date(2029, 1, 1),
    counterparty_id="CP-001",
    netting_set_id="NS-001",
    mark_to_market=125000.0
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
