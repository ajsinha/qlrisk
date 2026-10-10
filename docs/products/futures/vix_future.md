# VIX Future v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | VIX Future |
| **Product Class** | Futures - Volatility |
| **Asset Class** | Equity |
| **Product Type** | VIX_FUTURE |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Futures on the CBOE Volatility Index (VIX), which measures expected 30-day S&P 500 volatility. Used for volatility trading and portfolio hedging.

### Key Characteristics

- **Settlement:** Cash settled to VIX spot
- **Multiplier:** $1,000 per point
- **Term Structure:** Typically in contango
- **Roll Yield:** Negative (contango) or positive (backwardation)

---

## Mathematical Framework

### VIX Term Structure

Typically upward sloping (contango):

$$VIX_{future} > VIX_{spot}$$

### Roll Cost

$$Roll Cost = \frac{F_{near} - F_{far}}{F_{near}} \times \frac{365}{Days}$$

---

## Implementation Example

```python
from products.python.futures import VIXFuture

vix = VIXFuture(
    trade_id="VIX-001",
    contracts=20,
    contract_multiplier=1000.0,
    entry_price=18.5,
    expiry_date=date(2024, 2, 21),
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
