# Bond Future v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Bond Future |
| **Product Class** | Futures |
| **Asset Class** | Interest Rate |
| **Product Type** | BOND_FUTURE |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Futures contracts on government bonds with physical delivery of the cheapest-to-deliver (CTD) bond from a basket of eligible securities.

### US Treasury Futures

| Contract | Tenor | Exchange |
|----------|-------|----------|
| ZT | 2-Year | CBOT |
| ZF | 5-Year | CBOT |
| ZN | 10-Year | CBOT |
| ZB | 30-Year (T-Bond) | CBOT |
| UB | Ultra Bond | CBOT |

---

## Mathematical Framework

### Conversion Factor

$$CF = \frac{Price_{bond} \text{ if yield = 6\%}}{100}$$

### Cheapest-to-Deliver

$$CTD = \arg\min_i (P_i - CF_i \times F)$$

### Basis

$$Basis = P_{CTD} - CF_{CTD} \times F$$

### DV01

$$DV01_{future} \approx \frac{DV01_{CTD}}{CF_{CTD}}$$

---

## Implementation Example

```python
from products.python.futures import BondFuture

zn = BondFuture(
    trade_id="ZN-001",
    underlying="10Y_UST",
    contracts=50,
    entry_price=110.5,
    expiry_date=date(2024, 3, 19),
    ctd_bond_id="912810TM",
    conversion_factor=0.8523,
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
