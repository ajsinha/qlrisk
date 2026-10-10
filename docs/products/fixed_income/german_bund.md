# German Bund

<!-- generated:implementation -->
> **Implementation:** `GermanBund` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | German Bund (Bundesanleihe) |
| **Product Class** | Fixed Income - Government Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | GERMAN_BUND |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

German Bunds are debt securities issued by the German Federal Government (Bundesrepublik Deutschland). They are considered the benchmark for European government bonds and the risk-free rate for EUR-denominated assets due to Germany's strong credit rating and fiscal stability.

### Key Characteristics

- **Issuer:** Federal Republic of Germany
- **Currency:** EUR
- **Coupon Frequency:** Annual
- **Day Count:** ACT/ACT (ICMA)
- **Maturity:** 10 and 30 years (Bund); 2 years (Schatz); 5 years (Bobl)
- **Benchmark Status:** EUR risk-free benchmark

---

## German Government Securities

| Security | Maturity | Coupon |
|----------|----------|--------|
| **Bundesschatzanweisungen (Schatz)** | 2 years | Annual |
| **Bundesobligationen (Bobl)** | 5 years | Annual |
| **Bundesanleihen (Bund)** | 10, 30 years | Annual |

---

## Mathematical Framework

$$P = \sum_{i=1}^{n} \frac{C}{(1 + y)^i} + \frac{F}{(1 + y)^n}$$

Note: Annual coupon frequency (not semi-annual).

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import GermanBund
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = GermanBund("GERMAN-BUND-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
