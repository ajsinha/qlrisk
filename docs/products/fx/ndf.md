# Non-Deliverable Forward (NDF)

<!-- generated:implementation -->
> **Implementation:** `NonDeliverableForward` is priced by `price_fx_ndf` in `products/python/_pricing.py`. Product terms are keyword arguments: `pair`, `forward_rate`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Non-Deliverable Forward (NDF) |
| **Product Class** | Foreign Exchange |
| **Asset Class** | FX |
| **Product Type** | NDF |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Non-Deliverable Forward is a cash-settled FX forward used for currencies with capital controls or limited convertibility. Settlement is in a freely traded currency (usually USD) based on the difference between contracted and fixing rates.

### Common NDF Currencies

| Currency | Country |
|----------|---------|
| CNY | China |
| INR | India |
| KRW | South Korea |
| TWD | Taiwan |
| BRL | Brazil |

---

## Mathematical Framework

### Settlement Amount

$$Settlement = N \times \left(\frac{1}{F_{fix}} - \frac{1}{F_{contract}}\right)$$

Or equivalently:

$$Settlement = N \times \frac{F_{contract} - F_{fix}}{F_{fix}}$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import NonDeliverableForward
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = NonDeliverableForward("NON-DELIVERABLE-FORWARD-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.USD, "CP-1", pair="USDJPY", forward_rate=148.0)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
