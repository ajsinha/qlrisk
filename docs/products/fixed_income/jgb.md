# Japanese Government Bond (JGB) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Japanese Government Bond (JGB) |
| **Product Class** | Fixed Income - Government Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | JGB |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

Japanese Government Bonds (JGBs) are debt securities issued by the Japanese Government. Japan has one of the largest government bond markets globally. JGBs are denominated in JPY and pay semi-annual coupons.

### Key Characteristics

- **Issuer:** Government of Japan (Ministry of Finance)
- **Currency:** JPY
- **Coupon Frequency:** Semi-annual
- **Day Count:** ACT/365
- **Yield Curve Control:** BOJ targets 10-year JGB yields

---

## JGB Categories

| Type | Maturity |
|------|----------|
| Short-term | 6 months, 1 year |
| Medium-term | 2, 5 years |
| Long-term | 10 years |
| Super-long | 20, 30, 40 years |
| Inflation-Linked | 10 years |

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import JGB
from products.base import Currency, MarketData

jgb = JGB(
    trade_id="JGB-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2034, 1, 15),
    face_value=1000000000,  # ¥1B
    currency=Currency.JPY,
    counterparty_id="CPY-001",
    coupon_rate=0.005,  # 0.5%
    is_long=True
)

result = jgb.price(market_data)
print(f"YTM: {result.components['ytm']:.3%}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
