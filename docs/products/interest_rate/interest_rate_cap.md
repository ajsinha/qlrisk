# Interest Rate Cap

<!-- generated:implementation -->
> **Implementation:** `InterestRateCap` has its own pricer and constructor arguments (see the example and `help(qlrisk.products.python.InterestRateCap)`).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
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
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import InterestRateCap
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = InterestRateCap("CAP-1", d0, d0, date(2029, 10, 9), 10_000_000, Currency.USD, "CP-1", strike=0.045)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
