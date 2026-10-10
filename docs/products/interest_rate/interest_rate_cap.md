# Interest Rate Cap v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Interest Rate Cap |
| **Product Class** | Interest Rate Derivatives |
| **Asset Class** | Interest Rate |
| **Product Type** | CAP |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

An interest rate cap is a series of European call options (caplets) on an interest rate. It provides protection against rising interest rates by paying the holder when the reference rate exceeds the strike (cap) rate.

### Key Characteristics

- **Structure:** Portfolio of caplets
- **Payoff:** max(0, R - K) per period
- **Premium:** Paid upfront
- **Uses:** Hedging floating-rate debt

---

## Mathematical Framework

### Caplet Payoff

$$Payoff = N \times \tau \times \max(0, R - K)$$

### Black's Model (Caplet)

$$Caplet = N \times \tau \times DF(T) \times [F \times N(d_1) - K \times N(d_2)]$$

Where:

$$d_1 = \frac{\ln(F/K) + 0.5\sigma^2 T}{\sigma\sqrt{T}}$$

$$d_2 = d_1 - \sigma\sqrt{T}$$

### Cap Value

$$Cap = \sum_{i=1}^{n} Caplet_i$$

---

## Greeks

| Greek | Formula |
|-------|---------|
| Delta | $\sum_i N(d_1)_i$ |
| Gamma | $\sum_i \frac{n(d_1)_i}{F_i \sigma \sqrt{T_i}}$ |
| Vega | $\sum_i F_i \sqrt{T_i} n(d_1)_i$ |
| Theta | Time decay |

---

## Implementation Example

```python
from datetime import date
from products.python.interest_rate import InterestRateCap
from products.base import Currency, MarketData

cap = InterestRateCap(
    trade_id="CAP-001",
    trade_date=date(2024, 1, 15),
    effective_date=date(2024, 1, 17),
    maturity_date=date(2027, 1, 17),
    notional=50000000,
    strike=0.05,  # 5% cap rate
    currency=Currency.USD,
    counterparty_id="CPY-001",
    is_long=True,
    volatility=0.20
)

result = cap.price(market_data)
print(f"Premium: ${result.npv:,.2f}")
print(f"Vega: ${result.greeks['vega']:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
