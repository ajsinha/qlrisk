# French OAT (Obligations Assimilables du Trésor) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | French OAT |
| **Product Class** | Fixed Income - Government Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | FRENCH_OAT |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

French OATs (Obligations Assimilables du Trésor) are medium to long-term French government bonds issued by Agence France Trésor. They are the benchmark securities for French sovereign debt.

### Key Characteristics

- **Issuer:** French Republic (Agence France Trésor)
- **Currency:** EUR
- **Coupon Frequency:** Annual
- **Day Count:** ACT/ACT (ICMA)
- **Maturity:** 2 to 50 years

---

## OAT Types

| Type | Description |
|------|-------------|
| **OAT Standard** | Fixed-rate nominal bonds |
| **OATi** | Inflation-linked (French CPI) |
| **OAT€i** | Inflation-linked (Eurozone HICP) |

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import FrenchOAT
from products.base import Currency, MarketData

oat = FrenchOAT(
    trade_id="OAT-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2034, 1, 15),
    face_value=10000000,
    currency=Currency.EUR,
    counterparty_id="CPY-001",
    coupon_rate=0.0275,
    is_long=True
)

result = oat.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
