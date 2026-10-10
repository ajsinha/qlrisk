# Floating Rate Note (FRN) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Floating Rate Note (FRN) |
| **Product Class** | Fixed Income - Floating Rate Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | FRN |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

A Floating Rate Note is a debt instrument with a variable interest rate. The coupon is typically tied to a benchmark rate (SOFR, EURIBOR, etc.) plus a fixed spread. FRNs provide protection against rising interest rates.

### Key Characteristics

- **Coupon:** Reference rate + fixed spread
- **Reset Frequency:** Typically quarterly
- **Duration:** Very short (to next reset)
- **Rate Risk:** Minimal
- **Spread Risk:** Exposure to credit spread changes

---

## Common Reference Rates

| Rate | Currency | Description |
|------|----------|-------------|
| **SOFR** | USD | Secured Overnight Financing Rate |
| **SONIA** | GBP | Sterling Overnight Index Average |
| **€STR** | EUR | Euro Short-Term Rate |
| **TONA** | JPY | Tokyo Overnight Average Rate |

---

## Mathematical Framework

### Coupon Calculation

$$C_i = (R_i + s) \times \tau_i \times N$$

Where:
- $R_i$ = Reference rate for period $i$
- $s$ = Spread (margin)
- $\tau_i$ = Accrual fraction
- $N$ = Notional

### Valuation

FRNs reset to par at each fixing:

$$P \approx 100 + \frac{(R_0 + s - R_{market} - s_{market}) \times \tau}{1 + (R_{market} + s_{market}) \times \tau}$$

### Duration

Duration is approximately equal to time to next reset:

$$D \approx \tau_{next}$$

---

## Cap and Floor Features

Many FRNs include embedded options:

### Capped FRN

$$C = \min(R + s, Cap)$$

### Floored FRN

$$C = \max(R + s, Floor)$$

### Collared FRN

$$C = \min(\max(R + s, Floor), Cap)$$

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import FloatingRateNote
from products.base import Currency, MarketData, PaymentFrequency

frn = FloatingRateNote(
    trade_id="FRN-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2027, 1, 15),
    face_value=10000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    spread=0.0075,  # 75 bps over SOFR
    reference_rate="SOFR",
    reset_frequency=PaymentFrequency.QUARTERLY,
    issuer_name="Bank ABC",
    floor=0.0,
    cap=0.08,
    is_long=True
)

result = frn.price(market_data)
print(f"Current Coupon: {result.components['current_coupon']:.2%}")
print(f"Duration: {result.components['duration']:.2f}")
print(f"Spread DV01: ${result.greeks['spread_dv01']:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
