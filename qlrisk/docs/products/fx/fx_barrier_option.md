# FX Barrier Option v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | FX Barrier Option |
| **Product Class** | Foreign Exchange - Exotic |
| **Asset Class** | FX |
| **Product Type** | FX_BARRIER |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A barrier option is an FX option that is activated (knock-in) or deactivated (knock-out) when the underlying spot rate crosses a specified barrier level. Barriers trade at a discount to vanilla options.

### Barrier Types

| Type | Activation |
|------|------------|
| **Up-and-Out** | Knocked out if spot rises above barrier |
| **Up-and-In** | Activated if spot rises above barrier |
| **Down-and-Out** | Knocked out if spot falls below barrier |
| **Down-and-In** | Activated if spot falls below barrier |

---

## Mathematical Framework

### Closed-Form Solutions

For knock-out barriers:

$$BarrierCall = VanillaCall - Rebate \times P(barrier hit)$$

### Monte Carlo

For complex barriers:

$$V = DF \times E[\max(0, S_T - K) \times \mathbb{1}_{no barrier hit}]$$

---

## Implementation Example

```python
from datetime import date
from products.python.fx import FXBarrierOption
from products.base import Currency, MarketData, OptionType

barrier = FXBarrierOption(
    trade_id="FXBAR-001",
    trade_date=date(2024, 1, 15),
    expiry_date=date(2024, 7, 15),
    settlement_date=date(2024, 7, 17),
    base_currency=Currency.EUR,
    quote_currency=Currency.USD,
    base_notional=10000000,
    strike=1.10,
    barrier_level=1.15,
    barrier_type="up_and_out",
    counterparty_id="CPY-001",
    option_type=OptionType.CALL,
    is_long=True
)

result = barrier.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
