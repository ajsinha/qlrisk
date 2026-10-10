# Commodity Forward

<!-- generated:implementation -->
> **Implementation:** `CommodityForward` is priced by `price_commodity_forward` in `products/python/_pricing.py`. Product terms are keyword arguments: `commodity` (commodity_prices key), `strike`, `quantity`, `convenience_yield`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Commodity Forward |
| **Product Class** | Commodity Derivatives |
| **Asset Class** | Commodity |
| **Product Type** | COMMODITY_FORWARD |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Forward contract for commodity delivery at a future date.

---

## Mathematical Framework

### Forward Price

$$F = S \times e^{(r + c - y) \times T}$$

Where c = storage cost, y = convenience yield

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

## Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import CommodityForward
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = CommodityForward("COMMODITY-FORWARD-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.USD, "CP-1", commodity="WTI", strike=75.0)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```
