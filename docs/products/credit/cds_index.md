# CDS Index

<!-- generated:implementation -->
> **Implementation:** `CDSIndex` is priced by `price_cds` in `products/python/_pricing.py`. Product terms are keyword arguments: `reference` (credit curve), `coupon`, `recovery` (0.4), `is_buyer`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | CDS Index |
| **Product Class** | Credit Derivatives |
| **Asset Class** | Credit |
| **Product Type** | CDS_INDEX |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A CDS Index provides protection on a portfolio of reference entities. Major indices include CDX (North America), iTraxx (Europe), and regional variants.

### Major Indices

| Index | Region | Components |
|-------|--------|------------|
| CDX.NA.IG | North America | 125 IG names |
| CDX.NA.HY | North America | 100 HY names |
| iTraxx Europe | Europe | 125 IG names |
| iTraxx Crossover | Europe | 75 HY names |

---

## Mathematical Framework

### Index Spread

$$s_{index} = \sum_{i=1}^{n} w_i \times s_i$$

### Index Price

Quoted as price (e.g., 100.25):

$$Price = 100 + Duration \times (s_{index} - s_{coupon})$$

---

## SA-CCR Treatment

Index CDS use separate supervisory factors:

| Index Type | SF |
|------------|-----|
| IG Index | 0.38% |
| HY/SG Index | 1.06% |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import CDSIndex
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = CDSIndex("CDS-INDEX-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", reference="ACME", coupon=0.01)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
