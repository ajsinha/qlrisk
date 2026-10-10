# Buy/Sell Back

<!-- generated:implementation -->
> **Implementation:** `BuySellBack` is priced by `price_deposit` in `products/python/_pricing.py`. Product terms are keyword arguments: `rate`, `issuer`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Buy/Sell Back |
| **Product Class** | Securities Financing |
| **Asset Class** | Repo |
| **Product Type** | BUY_SELL_BACK |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Two separate outright transactions (spot purchase and forward sale) rather than a single repo agreement. Common in some European markets.

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

## Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import BuySellBack
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = BuySellBack("BUY-SELL-BACK-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.USD, "CP-1", rate=0.045)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```
