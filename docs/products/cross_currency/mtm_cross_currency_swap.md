# Mark-to-Market Cross-Currency Swap

<!-- generated:implementation -->
> **Implementation:** `MTMCrossCurrencySwap` is priced by `price_xccy_swap` in `products/python/_pricing.py`. Product terms are keyword arguments: `pair`, `foreign_curve`, `domestic_coupon`, `foreign_coupon`, `frequency`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | MTM Cross-Currency Swap |
| **Product Class** | Cross-Currency Derivatives |
| **Asset Class** | Interest Rate + FX |
| **Product Type** | MTM_XCCY |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Cross-currency swap with periodic FX reset. Reduces FX exposure through regular mark-to-market adjustments.

---

## SA-CCR Treatment

MTM feature reduces FX add-on by 50%.

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

## Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import MTMCrossCurrencySwap
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = MTMCrossCurrencySwap("MTM-CROSS-CURRENCY-SWAP-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", pair="EURUSD", foreign_curve="ESTR")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```
