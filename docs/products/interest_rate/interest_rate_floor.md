# Interest Rate Floor v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Interest Rate Floor |
| **Product Class** | Interest Rate Derivatives |
| **Asset Class** | Interest Rate |
| **Product Type** | FLOOR |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

An interest rate floor is a series of European put options (floorlets) on an interest rate. It provides protection against falling interest rates by paying the holder when the reference rate falls below the strike (floor) rate.

### Key Characteristics

- **Structure:** Portfolio of floorlets
- **Payoff:** max(0, K - R) per period
- **Premium:** Paid upfront
- **Uses:** Protecting floating-rate investments

---

## Mathematical Framework

### Floorlet Payoff

$$Payoff = N \times \tau \times \max(0, K - R)$$

### Black's Model (Floorlet)

$$Floorlet = N \times \tau \times DF(T) \times [K \times N(-d_2) - F \times N(-d_1)]$$

### Put-Call Parity

$$Cap - Floor = IRS$$

---

## Implementation Example

```python
from datetime import date
from products.python.interest_rate import InterestRateFloor
from products.base import Currency, MarketData

floor = InterestRateFloor(
    trade_id="FLOOR-001",
    trade_date=date(2024, 1, 15),
    effective_date=date(2024, 1, 17),
    maturity_date=date(2027, 1, 17),
    notional=50000000,
    strike=0.03,  # 3% floor rate
    currency=Currency.USD,
    counterparty_id="CPY-001",
    is_long=True,
    volatility=0.20
)

result = floor.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
