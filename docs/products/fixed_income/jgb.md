# Japanese Government Bond (JGB)

<!-- generated:implementation -->
> **Implementation:** `JGB` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Japanese Government Bond (JGB) |
| **Product Class** | Fixed Income - Government Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | JGB |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

Japanese Government Bonds (JGBs) are debt securities issued by the Japanese Government. Japan has one of the largest government bond markets globally. JGBs are denominated in JPY and pay semi-annual coupons.

### Key Characteristics

- **Issuer:** Government of Japan (Ministry of Finance)
- **Currency:** JPY
- **Coupon Frequency:** Semi-annual
- **Day Count:** ACT/365
- **Yield Curve Control:** BOJ targets 10-year JGB yields

---

## JGB Categories

| Type | Maturity |
|------|----------|
| Short-term | 6 months, 1 year |
| Medium-term | 2, 5 years |
| Long-term | 10 years |
| Super-long | 20, 30, 40 years |
| Inflation-Linked | 10 years |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import JGB
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = JGB("JGB-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
