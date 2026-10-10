# UK Gilt v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | UK Gilt (Gilt-Edged Securities) |
| **Product Class** | Fixed Income - Government Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | UK_GILT |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

UK Gilts are bonds issued by the UK Government through the Debt Management Office (DMO). The name "gilt-edged" reflects their historical status as a highly secure investment. Gilts are denominated in GBP and pay semi-annual coupons.

### Key Characteristics

- **Issuer:** UK Government (HM Treasury)
- **Currency:** GBP
- **Coupon Frequency:** Semi-annual
- **Day Count:** ACT/ACT (ICMA)
- **Settlement:** T+1
- **Primary Dealer System:** Gilt-Edged Market Makers (GEMMs)

---

## Types of Gilts

| Type | Description |
|------|-------------|
| **Conventional Gilts** | Fixed coupon, nominal redemption |
| **Index-Linked Gilts** | Inflation-linked (RPI) |
| **Undated Gilts** | Perpetual (largely redeemed) |

---

## Mathematical Framework

Same as standard fixed-rate bonds:

$$P = \sum_{i=1}^{n} \frac{C/2}{(1 + y/2)^i} + \frac{F}{(1 + y/2)^n}$$

### Gilt-Specific Conventions

- Accrued interest: ACT/ACT with ex-dividend period
- Ex-dividend period: 7 business days before coupon

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import UKGilt
from products.base import Currency, MarketData

gilt = UKGilt(
    trade_id="GILT-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2034, 1, 15),
    face_value=5000000,
    currency=Currency.GBP,
    counterparty_id="CPY-001",
    coupon_rate=0.035,
    is_long=True
)

result = gilt.price(market_data)
print(f"Price: {result.components['clean_price']:.4f}")
print(f"YTM: {result.components['ytm']:.2%}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
