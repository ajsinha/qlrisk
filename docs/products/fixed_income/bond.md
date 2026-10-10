# Bond (Base Class) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Bond (Generic) |
| **Product Class** | Fixed Income |
| **Asset Class** | Interest Rate |
| **Product Type** | BOND |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

The Bond class is the base implementation for all fixed income products. It provides core functionality for cash flow generation, pricing, duration, and risk calculations that are inherited by specific bond types.

### Core Features

- Cash flow generation
- YTM calculation (Brent's method)
- Duration and convexity
- DV01 and risk metrics
- Accrued interest

---

## Inheritance Hierarchy

```
Bond (Base)
├── TreasuryBill
├── TreasuryNote
├── TreasuryBond
├── TIPS
├── UKGilt
├── GermanBund
├── JGB
├── FrenchOAT
├── MunicipalBond
├── AgencyBond
├── CorporateBond
├── FloatingRateNote
├── ConvertibleBond
├── MBS
├── ABS
├── CDO
└── CLO
```

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import Bond
from products.base import Currency, MarketData

# Generic bond
bond = Bond(
    trade_id="BOND-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2034, 1, 15),
    face_value=1000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    coupon_rate=0.04,
    is_long=True
)

result = bond.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
