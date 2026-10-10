# Collateralized Debt Obligation (CDO) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Collateralized Debt Obligation (CDO) |
| **Product Class** | Fixed Income - Structured Credit |
| **Asset Class** | Credit |
| **Product Type** | CDO |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A CDO is a structured financial product that pools together cash flow-generating assets and repackages them into tranches with different risk/return profiles. The collateral can include bonds, loans, or other debt instruments.

### CDO Types

| Type | Collateral |
|------|------------|
| **CBO** | Bonds |
| **CLO** | Leveraged Loans |
| **CFO** | Cash flows |
| **Synthetic CDO** | Credit derivatives |

---

## Tranche Structure

| Tranche | Attachment | Detachment | Rating |
|---------|------------|------------|--------|
| **Super Senior** | 30% | 100% | AAA |
| **Senior** | 15% | 30% | AA/A |
| **Mezzanine** | 7% | 15% | BBB/BB |
| **Junior** | 3% | 7% | B |
| **Equity** | 0% | 3% | NR |

### Loss Allocation

Losses are absorbed starting from equity tranche upward.

---

## Mathematical Framework

### Expected Loss

$$EL = PD \times LGD \times EAD$$

### Tranche Loss

For a tranche with attachment $A$ and detachment $D$:

$$Loss_{tranche} = \max(0, \min(L - A, D - A))$$

### Correlation Impact

Higher default correlation → Higher senior tranche risk

---

## SA-CCR Treatment

CDO tranches require adjusted notional:

$$EN = Notional \times (D - A)$$

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import CDO
from products.base import Currency, MarketData

cdo = CDO(
    trade_id="CDO-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 1),
    maturity_date=date(2029, 1, 1),
    face_value=10000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    coupon_rate=0.06,
    attachment_point=0.07,
    detachment_point=0.15,
    pool_notional=500000000,
    is_long=True
)

result = cdo.price(market_data)
print(f"Expected Loss: ${result.components['expected_loss']:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
