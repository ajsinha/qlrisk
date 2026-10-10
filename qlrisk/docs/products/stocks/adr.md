# American Depositary Receipt (ADR) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | American Depositary Receipt |
| **Product Class** | Equities - Depositary Receipts |
| **Asset Class** | Equity |
| **Product Type** | ADR |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

ADRs are negotiable certificates representing shares of foreign companies trading on U.S. exchanges. They allow U.S. investors to own foreign stocks without dealing with foreign exchanges or currencies directly.

### ADR Levels

| Level | Exchange | SEC Registration |
|-------|----------|-----------------|
| Level I | OTC | Minimal |
| Level II | Listed | Full |
| Level III | Listed + Capital Raising | Full |

---

## Implementation Example

```python
from products.python.stocks import ADR

adr = ADR(
    trade_id="ADR-001",
    ticker="BABA",
    shares=5000,
    adr_ratio=8,  # 8 ADRs = 1 ordinary share
    underlying_currency=Currency.CNY,
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
