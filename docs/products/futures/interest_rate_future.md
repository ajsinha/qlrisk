# Interest Rate Future v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Interest Rate Future |
| **Product Class** | Futures |
| **Asset Class** | Interest Rate |
| **Product Type** | IR_FUTURE |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Futures on short-term interest rates, used for hedging and speculating on rate movements. Key instruments for curve construction.

### Major IR Futures

| Contract | Reference | Size | Exchange |
|----------|-----------|------|----------|
| SR3 | 3M SOFR | $1M | CME |
| SR1 | 1M SOFR | $5M | CME |
| FF | Fed Funds | $5M | CBOT |

---

## Mathematical Framework

### Price Convention

$$Price = 100 - Rate$$

### DV01

$$DV01 = Notional \times 0.0001 \times \frac{Days}{360}$$

For 3M SOFR: DV01 ≈ $25 per contract per bp

---

## SA-CCR Treatment

$$AddOn = 0.50\% \times Notional \times SD \times MF$$

---

## Implementation Example

```python
from products.python.futures import InterestRateFuture

sofr = InterestRateFuture(
    trade_id="SR3-001",
    reference_rate="SOFR_3M",
    contracts=100,
    contract_size=1000000,
    entry_price=95.25,  # Implied 4.75% rate
    expiry_date=date(2024, 6, 19),
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
