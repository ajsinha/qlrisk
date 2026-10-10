# Medium Term Note (MTN) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Medium Term Note (MTN) |
| **Product Class** | Fixed Income - Corporate Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | MEDIUM_TERM_NOTE |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Medium Term Notes are debt instruments issued under a shelf registration program, allowing issuers to offer notes with various maturities, typically ranging from 9 months to 30 years. MTNs provide flexibility in terms of structure and timing.

### Key Characteristics

- **Maturity:** 9 months to 30+ years
- **Shelf Registration:** SEC Rule 415
- **Continuous Offering:** Issued as needed
- **Customizable:** Tailored to investor needs
- **Distribution:** Primary dealer network

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import MediumTermNote
from products.base import Currency, MarketData

mtn = MediumTermNote(
    trade_id="MTN-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2029, 1, 15),
    face_value=5000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    coupon_rate=0.045,
    issuer_name="Major Bank",
    program_name="Global MTN Program",
    is_long=True
)

result = mtn.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
