# Asset-Backed Securities (ABS) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Asset-Backed Securities (ABS) |
| **Product Class** | Fixed Income - Securitized Products |
| **Asset Class** | Interest Rate |
| **Product Type** | ABS |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Asset-Backed Securities are bonds backed by pools of assets other than mortgages. Common collateral includes auto loans, credit card receivables, student loans, and equipment leases. The cash flows from these assets support the bond payments.

### Common ABS Types

| Collateral | Typical Maturity | Prepayment Risk |
|------------|------------------|-----------------|
| **Auto Loans** | 2-5 years | Moderate |
| **Credit Cards** | Revolving | Low |
| **Student Loans** | 10-25 years | Moderate |
| **Equipment Leases** | 3-7 years | Low |

---

## Structure

ABS typically have tranched structures:

| Tranche | Rating | Priority |
|---------|--------|----------|
| Class A | AAA | Senior |
| Class B | AA/A | Mezzanine |
| Class C | BBB | Junior |
| Residual | NR | Equity |

### Credit Enhancement

- **Overcollateralization**
- **Subordination**
- **Excess spread**
- **Reserve accounts**

---

## Mathematical Framework

### Waterfall Mechanics

1. Pay senior interest
2. Pay senior principal
3. Pay mezzanine interest
4. Pay mezzanine principal
5. Junior tranches
6. Residual cash flow

### Loss Allocation

Losses are allocated in reverse order of seniority.

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import ABS
from products.base import Currency, MarketData

abs_auto = ABS(
    trade_id="ABS-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 1),
    maturity_date=date(2029, 1, 1),
    face_value=10000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    coupon_rate=0.045,
    collateral_type="auto",
    tranche="A",
    credit_enhancement=0.15,
    is_long=True
)

result = abs_auto.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
