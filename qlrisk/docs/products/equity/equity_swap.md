# Equity Swap v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Equity Swap |
| **Product Class** | Equity Derivatives |
| **Asset Class** | Equity |
| **Product Type** | EQUITY_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

An Equity Swap exchanges the return on an equity or equity index for a fixed or floating interest rate. It provides synthetic equity exposure without direct ownership.

### Key Characteristics

- **Equity Leg:** Total return (price + dividends)
- **Funding Leg:** SOFR + spread
- **No Initial Exchange:** Synthetic position
- **Mark-to-Market:** Periodic resets

---

## Mathematical Framework

### Equity Leg Value

$$V_{equity} = N \times \frac{S_t - S_0}{S_0}$$

### Total Return

$$TR = \frac{S_t - S_0 + Dividends}{S_0}$$

---

## SA-CCR Treatment

$$AddOn = SF_{equity} \times |Delta| \times Notional \times MF$$

Where SF = 32% (single) or 20% (index)

---

## Implementation Example

```python
from datetime import date
from products.python.equity import EquitySwap
from products.base import Currency, MarketData

eq_swap = EquitySwap(
    trade_id="EQSWP-001",
    trade_date=date(2024, 1, 15),
    effective_date=date(2024, 1, 17),
    maturity_date=date(2025, 1, 17),
    notional=25000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    underlying="SPX",
    initial_price=4800,
    funding_spread=0.0030,
    is_equity_receiver=True
)

result = eq_swap.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
