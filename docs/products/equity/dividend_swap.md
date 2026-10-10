# Dividend Swap v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Dividend Swap |
| **Product Class** | Equity Derivatives |
| **Asset Class** | Equity |
| **Product Type** | DIVIDEND_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Dividend Swap exchanges realized dividends for a fixed payment. It provides pure dividend exposure without equity price risk.

### Key Characteristics

- **Floating Leg:** Actual dividends received
- **Fixed Leg:** Agreed dividend rate
- **Uses:** Dividend hedging, speculation

---

## Mathematical Framework

### Swap Value

$$V = N \times (D_{realized} - D_{strike}) \times DF$$

---

## Implementation Example

```python
from datetime import date
from products.python.equity import DividendSwap
from products.base import Currency, MarketData

div_swap = DividendSwap(
    trade_id="DIVSWP-001",
    trade_date=date(2024, 1, 15),
    effective_date=date(2024, 1, 17),
    maturity_date=date(2025, 1, 17),
    underlying="SPX",
    strike_dividend=60.0,  # 60 index points
    notional=1000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    is_dividend_receiver=True
)

result = div_swap.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
