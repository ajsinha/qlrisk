# Floating Rate Note (FRN) v1.2.0

<!-- generated:implementation -->
> **Implementation:** `FloatingRateNote` is priced by `price_frn` in `products/python/_pricing.py`. Product terms are keyword arguments: `index`, `spread`, `frequency` (4), `issuer`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

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
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import FloatingRateNote
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = FloatingRateNote("FLOATING-RATE-NOTE-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", index="SOFR", spread=0.01, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
