# Equity Forward v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Equity Forward |
| **Product Class** | Equity Derivatives |
| **Asset Class** | Equity |
| **Product Type** | EQUITY_FORWARD |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

An Equity Forward is a contract to buy or sell an equity or index at a future date at a predetermined price.

---

## Mathematical Framework

### Forward Price

$$F = S \times e^{(r - q) \times T}$$

### NPV

$$NPV = (F_{market} - F_{contract}) \times e^{-rT} \times N$$

---

## Implementation Example

```python
from datetime import date
from products.python.equity import EquityForward
from products.base import Currency, MarketData

eq_fwd = EquityForward(
    trade_id="EQFWD-001",
    trade_date=date(2024, 1, 15),
    settlement_date=date(2024, 7, 15),
    underlying="SPX",
    forward_price=4900,
    notional=10000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    is_long=True
)

result = eq_fwd.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
