# Warrant v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Warrant |
| **Product Class** | Equities - Options |
| **Asset Class** | Equity |
| **Product Type** | WARRANT |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A warrant is a long-term option issued by a company giving the holder the right to buy shares at a specified price. Unlike exchange-traded options, warrants are issued by the company and may result in dilution.

### Key Characteristics

- **Long-term:** Often 5-10+ years
- **Company-issued:** New shares created on exercise
- **Dilution:** Affects existing shareholders
- **Leverage:** Lower cost than shares

---

## Mathematical Framework

### Black-Scholes Adjusted for Dilution

$$W = \frac{1}{1 + \frac{m}{n}} \times BS(S, K, T, r, \sigma)$$

Where m = warrants outstanding, n = shares outstanding

---

## Implementation Example

```python
from products.python.stocks import Warrant

warrant = Warrant(
    trade_id="WRT-001",
    ticker="SPCE-WS",
    warrants=50000,
    strike=11.50,
    expiry_date=date(2028, 1, 1),
    warrant_ratio=1.0,  # 1 warrant = 1 share
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
