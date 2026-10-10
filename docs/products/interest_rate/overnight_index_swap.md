# Overnight Index Swap (OIS)

<!-- generated:implementation -->
> **Implementation:** `OvernightIndexSwap` has its own pricer and constructor arguments (see the example and `help(qlrisk.products.python.OvernightIndexSwap)`).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Overnight Index Swap (OIS) |
| **Product Class** | Interest Rate Derivatives |
| **Asset Class** | Interest Rate |
| **Product Type** | OIS |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

An Overnight Index Swap is an interest rate swap where the floating leg is tied to an overnight rate index (SOFR, SONIA, €STR, TONA). OIS rates are used to derive risk-free discount curves and measure funding costs.

### Key Characteristics

- **Floating Rate:** Compounded overnight rate
- **Near Risk-Free:** Based on secured overnight rates
- **Benchmark:** Primary curve for discounting
- **Typical Tenors:** 1 week to 30 years

---

## Reference Rates

| Currency | Rate | Description |
|----------|------|-------------|
| USD | SOFR | Secured Overnight Financing Rate |
| EUR | €STR | Euro Short-Term Rate |
| GBP | SONIA | Sterling Overnight Index Average |
| JPY | TONA | Tokyo Overnight Average Rate |

---

## Mathematical Framework

### Compounded Overnight Rate

$$R_{compound} = \prod_{i=1}^{n} (1 + r_i \times d_i) - 1$$

Where:
- $r_i$ = Overnight rate on day $i$
- $d_i$ = Day count fraction (1/360 or 1/365)

### OIS Pricing

Same as standard IRS but floating leg uses compounded overnight rates.

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import OvernightIndexSwap
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = OvernightIndexSwap("OIS-1", d0, d0, date(2028, 10, 9), 10_000_000, Currency.USD, "CP-1", fixed_rate=0.042)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
