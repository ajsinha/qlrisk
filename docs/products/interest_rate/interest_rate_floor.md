# Interest Rate Floor

<!-- generated:implementation -->
> **Implementation:** `InterestRateFloor` has its own pricer and constructor arguments (see the example and `help(qlrisk.products.python.InterestRateFloor)`).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Interest Rate Floor |
| **Product Class** | Interest Rate Derivatives |
| **Asset Class** | Interest Rate |
| **Product Type** | FLOOR |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

An interest rate floor is a series of European put options (floorlets) on an interest rate. It provides protection against falling interest rates by paying the holder when the reference rate falls below the strike (floor) rate.

### Key Characteristics

- **Structure:** Portfolio of floorlets
- **Payoff:** max(0, K - R) per period
- **Premium:** Paid upfront
- **Uses:** Protecting floating-rate investments

---

## Mathematical Framework

### Floorlet Payoff

$$Payoff = N \times \tau \times \max(0, K - R)$$

### Black's Model (Floorlet)

$$Floorlet = N \times \tau \times DF(T) \times [K \times N(-d_2) - F \times N(-d_1)]$$

### Put-Call Parity

$$Cap - Floor = IRS$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import InterestRateFloor
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = InterestRateFloor("FLOOR-1", d0, d0, date(2029, 10, 9), 10_000_000, Currency.USD, "CP-1", strike=0.035)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
