# FX Forward v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | FX Forward |
| **Product Class** | Foreign Exchange |
| **Asset Class** | FX |
| **Product Type** | FX_FORWARD |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

An FX Forward is a contract to exchange currencies at a predetermined rate on a future date. It locks in an exchange rate for future delivery, protecting against currency fluctuations.

### Key Characteristics

- **Settlement:** Physical delivery of currencies
- **Customizable:** Any amount, date, currency pair
- **No Upfront Premium:** Zero NPV at inception
- **Uses:** Hedging, speculation

---

## Mathematical Framework

### Forward Rate (Covered Interest Parity)

$$F = S \times \frac{1 + r_d \times T}{1 + r_f \times T}$$

Or in continuous compounding:

$$F = S \times e^{(r_d - r_f) \times T}$$

Where:
- $S$ = Spot rate
- $r_d$ = Domestic interest rate
- $r_f$ = Foreign interest rate
- $T$ = Time to maturity

### Forward Points

$$Forward Points = (F - S) \times 10000$$

### NPV

$$NPV = N_{base} \times (F_{market} - F_{contract}) \times DF$$

---

## SA-CCR Treatment

$$AddOn_{FX} = SF_{FX} \times Notional \times MF$$

Where $SF_{FX} = 4.0\%$

---

## Implementation Example

```python
from datetime import date
from products.python.fx import FXForward
from products.base import Currency, MarketData

fx_fwd = FXForward(
    trade_id="FXFWD-001",
    trade_date=date(2024, 1, 15),
    settlement_date=date(2024, 7, 15),
    base_currency=Currency.EUR,
    quote_currency=Currency.USD,
    base_notional=10000000,  # €10M
    forward_rate=1.0850,
    counterparty_id="CPY-001",
    is_buy_base=True  # Buy EUR, sell USD
)

market_data = MarketData(
    valuation_date=date(2024, 4, 15),
    fx_spots={"EURUSD": 1.0750}
)

result = fx_fwd.price(market_data)
print(f"NPV: ${result.npv:,.2f}")
print(f"Forward Points: {result.components['forward_points']:.0f}")
```

---

## QuantLib Implementation

```python
from products.qlib.fx import FXForwardQL

fx_fwd_ql = FXForwardQL(
    trade_id="FXFWD-QL-001",
    trade_date=date(2024, 1, 15),
    settlement_date=date(2024, 7, 15),
    base_currency=Currency.EUR,
    quote_currency=Currency.USD,
    base_notional=10000000,
    forward_rate=1.0850,
    counterparty_id="CPY-001",
    is_buy_base=True
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
