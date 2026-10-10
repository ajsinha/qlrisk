# Forward Rate Agreement (FRA) v1.2.0

<!-- generated:implementation -->
> **Implementation:** `ForwardRateAgreement` has its own pricer and constructor arguments (see the example and `help(qlrisk.products.python.ForwardRateAgreement)`).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

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
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import ForwardRateAgreement
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = ForwardRateAgreement("FRA-1", d0, date(2027, 4, 7), date(2027, 4, 9), date(2027, 10, 9), 10_000_000, Currency.USD, "CP-1", fra_rate=0.043)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
