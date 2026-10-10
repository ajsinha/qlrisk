# Total Return Swap (TRS)

<!-- generated:implementation -->
> **Implementation:** `TotalReturnSwap` is priced by `price_total_return` in `products/python/_pricing.py`. Product terms are keyword arguments: `ticker` (equity) or `issuer` + `coupon` (bond), `spread`, `initial_price`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Total Return Swap (TRS) |
| **Product Class** | Credit Derivatives |
| **Asset Class** | Credit |
| **Product Type** | TRS |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Total Return Swap transfers the total economic performance of a reference asset (price changes plus income) to the receiver in exchange for a funding rate. It provides synthetic exposure without ownership.

### Key Characteristics

- **Total Return Leg:** Price appreciation + coupons/dividends
- **Funding Leg:** Reference rate + spread
- **No Initial Exchange:** Synthetic ownership
- **Uses:** Leverage, balance sheet management

---

## Mathematical Framework

### Total Return

$$TR = \Delta P + Coupons/Dividends$$

### TRS Spread

Fair spread $s$ satisfies:

$$E[TR] = (r + s) \times N \times T$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import TotalReturnSwap
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = TotalReturnSwap("TOTAL-RETURN-SWAP-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", ticker="AAPL", spread=0.005)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
