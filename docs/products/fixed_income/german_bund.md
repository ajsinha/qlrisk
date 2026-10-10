# German Bund v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | German Bund (Bundesanleihe) |
| **Product Class** | Fixed Income - Government Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | GERMAN_BUND |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

German Bunds are debt securities issued by the German Federal Government (Bundesrepublik Deutschland). They are considered the benchmark for European government bonds and the risk-free rate for EUR-denominated assets due to Germany's strong credit rating and fiscal stability.

### Key Characteristics

- **Issuer:** Federal Republic of Germany
- **Currency:** EUR
- **Coupon Frequency:** Annual
- **Day Count:** ACT/ACT (ICMA)
- **Maturity:** 10 and 30 years (Bund); 2 years (Schatz); 5 years (Bobl)
- **Benchmark Status:** EUR risk-free benchmark

---

## German Government Securities

| Security | Maturity | Coupon |
|----------|----------|--------|
| **Bundesschatzanweisungen (Schatz)** | 2 years | Annual |
| **Bundesobligationen (Bobl)** | 5 years | Annual |
| **Bundesanleihen (Bund)** | 10, 30 years | Annual |

---

## Mathematical Framework

$$P = \sum_{i=1}^{n} \frac{C}{(1 + y)^i} + \frac{F}{(1 + y)^n}$$

Note: Annual coupon frequency (not semi-annual).

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import GermanBund
from products.base import Currency, MarketData

bund = GermanBund(
    trade_id="BUND-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2034, 1, 15),
    face_value=10000000,
    currency=Currency.EUR,
    counterparty_id="CPY-001",
    coupon_rate=0.025,
    is_long=True
)

result = bund.price(market_data)
print(f"YTM: {result.components['ytm']:.2%}")
print(f"Duration: {result.components['modified_duration']:.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
