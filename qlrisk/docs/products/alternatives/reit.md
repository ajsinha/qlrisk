# Real Estate Investment Trust (REIT) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | REIT |
| **Product Class** | Real Estate |
| **Asset Class** | Alternative |
| **Product Type** | REIT |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

REITs are companies that own, operate, or finance income-producing real estate. They must distribute 90%+ of taxable income as dividends.

### REIT Types

| Type | Focus |
|------|-------|
| Equity REIT | Own properties |
| Mortgage REIT | Invest in mortgages/MBS |
| Hybrid REIT | Both |

### Sectors

- Residential (apartments)
- Office
- Retail
- Industrial/Logistics
- Healthcare
- Data Centers
- Cell Towers

---

## Key Metrics

| Metric | Description |
|--------|-------------|
| FFO | Funds From Operations |
| AFFO | Adjusted FFO |
| NAV | Net Asset Value |
| Cap Rate | NOI / Property Value |

---

## Implementation Example

```python
from products.python.alternatives import REIT

reit = REIT(
    trade_id="REIT-001",
    ticker="PLD",
    shares=5000,
    purchase_price=125.0,
    sector="industrial",
    reit_type="equity",
    dividend_yield=0.028,
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
