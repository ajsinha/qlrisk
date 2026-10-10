# Cross-Currency Swap v1.2.0

<!-- generated:implementation -->
> **Implementation:** `CrossCurrencySwap` is priced by `price_xccy_swap` in `products/python/_pricing.py`. Product terms are keyword arguments: `pair`, `foreign_curve`, `domestic_coupon`, `foreign_coupon`, `frequency`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Cross-Currency Swap |
| **Product Class** | Cross-Currency Derivatives |
| **Asset Class** | Interest Rate + FX |
| **Product Type** | XCCY_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Cross-Currency Swap exchanges interest payments in different currencies. Includes initial and final exchange of principals at spot rate.

### Key Characteristics

- **Principal Exchange:** At start and maturity
- **Interest Payments:** In respective currencies
- **Basis Spread:** Additional spread on one leg
- **Uses:** Funding, hedging currency risk

---

## SA-CCR Treatment

XCCY swaps have both IR and FX components:

$$AddOn = AddOn_{IR,ccy1} + AddOn_{IR,ccy2} + AddOn_{FX}$$

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

## Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import CrossCurrencySwap
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = CrossCurrencySwap("CROSS-CURRENCY-SWAP-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", pair="EURUSD", foreign_curve="ESTR")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```
