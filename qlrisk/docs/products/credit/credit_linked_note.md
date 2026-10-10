# Credit Linked Note (CLN) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Credit Linked Note (CLN) |
| **Product Class** | Credit Derivatives |
| **Asset Class** | Credit |
| **Product Type** | CLN |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Credit Linked Note is a funded credit derivative combining a bond with an embedded CDS. The investor receives an enhanced yield but loses principal if a credit event occurs on the reference entity.

### Key Characteristics

- **Funded:** Investor provides principal upfront
- **Enhanced Yield:** Credit spread above risk-free
- **Principal at Risk:** Loss upon credit event
- **Uses:** Yield enhancement, credit exposure

---

## Mathematical Framework

### CLN Value

$$CLN = Bond Floor - Embedded CDS$$

### Coupon

$$Coupon = r_{rf} + Credit Spread$$

---

## Implementation Example

```python
from datetime import date
from products.python.credit import CreditLinkedNote
from products.base import Currency, MarketData

cln = CreditLinkedNote(
    trade_id="CLN-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2029, 1, 15),
    face_value=5000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    reference_entity="ABC Corp",
    coupon_rate=0.06,  # 6% (includes credit spread)
    recovery_rate=0.40,
    is_long=True
)

result = cln.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
