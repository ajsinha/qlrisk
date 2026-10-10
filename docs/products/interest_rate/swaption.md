# Swaption v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Swaption (Swap Option) |
| **Product Class** | Interest Rate Derivatives |
| **Asset Class** | Interest Rate |
| **Product Type** | SWAPTION |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

A swaption is an option to enter into an interest rate swap at a future date. A payer swaption gives the right to enter a payer swap (pay fixed); a receiver swaption gives the right to enter a receiver swap (receive fixed).

### Key Characteristics

- **Types:** Payer vs Receiver
- **Exercise:** European, Bermudan, or American
- **Settlement:** Physical or cash
- **Expiry x Tenor:** e.g., 1Y x 5Y = 1-year option into 5-year swap

---

## Mathematical Framework

### Black's Model

$$Swaption = A \times [S \times N(\pm d_1) - K \times N(\pm d_2)]$$

Where:
- $A$ = Annuity factor = $\sum \tau_i \times DF(t_i)$
- $S$ = Forward swap rate
- $K$ = Strike rate
- $+$ for payer, $-$ for receiver

$$d_1 = \frac{\ln(S/K) + 0.5\sigma^2 T}{\sigma\sqrt{T}}$$

### Normal (Bachelier) Model

Alternative for low/negative rates:

$$Swaption = A \times \sigma \sqrt{T} \times [d \times N(d) + n(d)]$$

Where $d = (S - K) / (\sigma \sqrt{T})$

---

## Volatility

| Type | Description |
|------|-------------|
| **Black Vol** | Lognormal, percentage terms |
| **Normal Vol** | Basis points |

Conversion:
$$\sigma_{normal} \approx \sigma_{Black} \times S$$

---

## Implementation Example

```python
from datetime import date
from products.python.interest_rate import Swaption
from products.base import Currency, MarketData

# 1Y x 5Y payer swaption
swaption = Swaption(
    trade_id="SWPTN-001",
    trade_date=date(2024, 1, 15),
    option_expiry=date(2025, 1, 15),
    swap_effective=date(2025, 1, 17),
    swap_maturity=date(2030, 1, 17),
    notional=100000000,
    strike=0.04,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    is_payer=True,
    exercise_type="european",
    volatility=0.25
)

result = swaption.price(market_data)
print(f"Premium: ${result.npv:,.2f}")
print(f"Delta: {result.greeks['delta']:.2f}")
print(f"Vega: ${result.greeks['vega']:,.2f}")
```

---

## QuantLib Implementation

```python
from products.qlib.interest_rate import SwaptionQL

swaption_ql = SwaptionQL(
    trade_id="SWPTN-QL-001",
    trade_date=date(2024, 1, 15),
    option_expiry=date(2025, 1, 15),
    swap_effective=date(2025, 1, 17),
    swap_maturity=date(2030, 1, 17),
    notional=100000000,
    strike=0.04,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    is_payer=True
)

result_ql = swaption_ql.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
