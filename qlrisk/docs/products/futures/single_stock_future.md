# Single Stock Future v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Single Stock Future |
| **Product Class** | Futures |
| **Asset Class** | Equity |
| **Product Type** | SSF |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Futures contract on individual stocks, providing leveraged exposure to single-name equity price movements.

### Key Characteristics

- **Contract Size:** Typically 100 shares
- **Settlement:** Physical or cash
- **Margin:** Lower capital than stock
- **Dividend:** Reflected in pricing

---

## Mathematical Framework

### Forward Price

$$F = S \times e^{(r - q) \times T}$$

Or discrete dividends:

$$F = (S - PV(Dividends)) \times e^{r \times T}$$

---

## SA-CCR Treatment

Single stock futures use 32% SF:

$$AddOn = 32\% \times Delta \times Notional \times MF$$

---

## Implementation Example

```python
from products.python.futures import SingleStockFuture

ssf = SingleStockFuture(
    trade_id="SSF-001",
    underlying="AAPL",
    contracts=50,
    contract_size=100,
    entry_price=185.0,
    expiry_date=date(2024, 3, 15),
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
