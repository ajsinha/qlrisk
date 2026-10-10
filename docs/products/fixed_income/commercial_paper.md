# Commercial Paper v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Commercial Paper (CP) |
| **Product Class** | Fixed Income - Money Market |
| **Asset Class** | Interest Rate |
| **Product Type** | COMMERCIAL_PAPER |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Commercial paper is short-term, unsecured promissory notes issued by corporations to meet short-term funding needs. It is typically issued at a discount to face value and matures in 1 to 270 days.

### Key Characteristics

- **Maturity:** 1 to 270 days
- **Minimum Denomination:** $100,000 (typically $1M+)
- **Unsecured:** No collateral backing
- **Credit-Dependent:** Only high-quality issuers
- **Discount Instrument:** Zero-coupon structure

---

## Pricing

$$P = \frac{F}{1 + r \times \frac{days}{360}}$$

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import CommercialPaper
from products.base import Currency, MarketData

cp = CommercialPaper(
    trade_id="CP-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2024, 4, 15),
    face_value=10000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    discount_rate=0.0535,
    issuer_name="ABC Corp",
    credit_rating="A-1",
    is_long=True
)

result = cp.price(market_data)
print(f"Price: ${result.npv:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
