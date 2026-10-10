# Preferred Stock v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Preferred Stock |
| **Product Class** | Equities - Hybrid |
| **Asset Class** | Equity |
| **Product Type** | PREFERRED_STOCK |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Preferred stock is a hybrid security with characteristics of both equity and debt. It pays fixed dividends with priority over common stock but typically has no voting rights.

### Types

| Type | Feature |
|------|---------|
| Cumulative | Missed dividends accumulate |
| Non-Cumulative | Missed dividends lost |
| Participating | Share in excess profits |
| Convertible | Can convert to common |
| Callable | Issuer can redeem |

---

## Mathematical Framework

### Valuation (Perpetual)

$$P = \frac{D}{r}$$

### Convertible Preferred

$$P = \max(P_{preferred}, CR \times S_{common})$$

---

## Implementation Example

```python
from products.python.stocks import PreferredStock

preferred = PreferredStock(
    trade_id="PREF-001",
    ticker="BAC-PK",
    shares=10000,
    par_value=25.0,
    dividend_rate=0.06,  # 6% of par
    is_cumulative=True,
    is_convertible=True,
    conversion_ratio=2.5,
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
