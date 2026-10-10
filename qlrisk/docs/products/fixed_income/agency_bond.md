# Agency Bond v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Agency Bond |
| **Product Class** | Fixed Income - Agency Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | AGENCY_BOND |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Agency bonds are debt securities issued by government-sponsored enterprises (GSEs) and federal agencies. While not directly backed by the U.S. government, they carry an implicit government guarantee (for GSEs) or explicit guarantee (for federal agencies).

### Key Issuers

| Agency | Type | Guarantee |
|--------|------|-----------|
| **Fannie Mae (FNMA)** | GSE | Implicit |
| **Freddie Mac (FHLMC)** | GSE | Implicit |
| **Federal Home Loan Banks (FHLB)** | GSE | Implicit |
| **Ginnie Mae (GNMA)** | Federal | Explicit |
| **Tennessee Valley Authority (TVA)** | Federal | Implicit |

---

## Characteristics

- **Spread:** Trade at a small spread to Treasuries
- **Call Features:** Many are callable
- **Step-Up Coupons:** Common structure
- **Liquidity:** Very liquid secondary market

---

## Callable Bond Pricing

For callable agencies:

$$P = P_{bullet} - C_{call}$$

Where $C_{call}$ is the embedded call option value.

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import AgencyBond
from products.base import Currency, MarketData

agency = AgencyBond(
    trade_id="AGENCY-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2029, 1, 15),
    face_value=5000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    coupon_rate=0.045,
    issuer="FNMA",
    is_callable=True,
    call_date=date(2026, 1, 15),
    call_price=100.0,
    is_long=True
)

result = agency.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
