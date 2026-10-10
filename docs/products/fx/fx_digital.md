# FX Digital Option v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | FX Digital Option |
| **Product Class** | Foreign Exchange - Exotic |
| **Asset Class** | FX |
| **Product Type** | FX_DIGITAL |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

An FX Digital (Binary) option pays a fixed amount if the underlying spot rate is above (call) or below (put) the strike at expiration. The payoff is all-or-nothing.

### Key Characteristics

- **Fixed Payout:** Predetermined amount
- **Binary Payoff:** 0 or fixed amount
- **High Gamma:** Near strike at expiry
- **Pin Risk:** Risk near strike

---

## Mathematical Framework

### Digital Call

$$Digital_{call} = DF \times Payout \times N(d_2)$$

### Digital Put

$$Digital_{put} = DF \times Payout \times N(-d_2)$$

Where $d_2$ is from Garman-Kohlhagen.

---

## Implementation Example

```python
from datetime import date
from products.python.fx import FXDigitalOption
from products.base import Currency, MarketData

digital = FXDigitalOption(
    trade_id="FXDIG-001",
    trade_date=date(2024, 1, 15),
    expiry_date=date(2024, 7, 15),
    base_currency=Currency.EUR,
    quote_currency=Currency.USD,
    payout=1000000,  # $1M payout
    strike=1.10,
    counterparty_id="CPY-001",
    is_call=True,
    is_long=True
)

result = digital.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
