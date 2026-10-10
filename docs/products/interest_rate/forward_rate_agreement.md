# Forward Rate Agreement (FRA) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Forward Rate Agreement (FRA) |
| **Product Class** | Interest Rate Derivatives |
| **Asset Class** | Interest Rate |
| **Product Type** | FRA |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Forward Rate Agreement is an OTC derivative that allows parties to lock in an interest rate for a future period. FRAs are cash-settled and represent the simplest form of interest rate derivative.

### Key Characteristics

- **Settlement:** Cash-settled at fixing date
- **Single Period:** One interest period
- **Notation:** "3x6 FRA" = 3-month forward, 6-month maturity
- **Uses:** Hedging, speculation on rate movements

---

## Mathematical Framework

### FRA Rate

The fair FRA rate is derived from forward rates:

$$F = \frac{DF(t_s) / DF(t_e) - 1}{\tau}$$

### Settlement Amount

$$Settlement = \frac{N \times (R - F) \times \tau}{1 + R \times \tau}$$

Where:
- $R$ = Fixing rate at settlement
- $F$ = FRA contract rate
- $\tau$ = Day count fraction

---

## Implementation Example

```python
from datetime import date
from products.python.interest_rate import ForwardRateAgreement
from products.base import Currency, MarketData

fra = ForwardRateAgreement(
    trade_id="FRA-001",
    trade_date=date(2024, 1, 15),
    fixing_date=date(2024, 4, 15),
    effective_date=date(2024, 4, 17),
    maturity_date=date(2024, 7, 17),
    notional=25000000,
    fra_rate=0.048,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    is_long=True
)

result = fra.price(market_data)
print(f"NPV: ${result.npv:,.2f}")
print(f"Forward Rate: {result.components['forward_rate']:.2%}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
