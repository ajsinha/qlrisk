# FX Swap v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | FX Swap |
| **Product Class** | Foreign Exchange |
| **Asset Class** | FX |
| **Product Type** | FX_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

An FX Swap combines a spot transaction with a forward transaction in opposite directions. It's used to extend or roll forward positions, manage funding, and adjust currency exposure timing.

### Key Characteristics

- **Two Legs:** Near leg (spot) + Far leg (forward)
- **Opposite Directions:** Buy/sell vs sell/buy
- **Same Amount:** Notional unchanged
- **Swap Points:** Difference between spot and forward

---

## Mathematical Framework

### FX Swap Rate

$$Swap Points = F - S = S \times (e^{(r_d - r_f) \times T} - 1)$$

### Net Cost

$$Cost = \frac{Swap Points \times N \times Days}{10000 \times 365}$$

---

## Implementation Example

```python
from datetime import date
from products.python.fx import FXSwap
from products.base import Currency, MarketData

fx_swap = FXSwap(
    trade_id="FXSWP-001",
    trade_date=date(2024, 1, 15),
    near_date=date(2024, 1, 17),
    far_date=date(2024, 4, 17),
    base_currency=Currency.USD,
    quote_currency=Currency.JPY,
    base_notional=50000000,
    near_rate=148.50,
    far_rate=147.80,
    counterparty_id="CPY-001",
    buy_base_near=True
)

result = fx_swap.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
