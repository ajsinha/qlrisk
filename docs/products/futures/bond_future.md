# Bond Future

<!-- generated:implementation -->
> **Implementation:** `BondFuture` is priced by `price_bond_future` in `products/python/_pricing.py`. Product terms are keyword arguments: `bond_coupon`, `bond_maturity_years`, `conversion_factor`, `strike`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Bond Future |
| **Product Class** | Futures |
| **Asset Class** | Interest Rate |
| **Product Type** | BOND_FUTURE |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Futures contracts on government bonds with physical delivery of the cheapest-to-deliver (CTD) bond from a basket of eligible securities.

### US Treasury Futures

| Contract | Tenor | Exchange |
|----------|-------|----------|
| ZT | 2-Year | CBOT |
| ZF | 5-Year | CBOT |
| ZN | 10-Year | CBOT |
| ZB | 30-Year (T-Bond) | CBOT |
| UB | Ultra Bond | CBOT |

---

## Mathematical Framework

### Conversion Factor

$$CF = \frac{Price_{bond} \text{ if yield = 6\%}}{100}$$

### Cheapest-to-Deliver

$$CTD = \arg\min_i (P_i - CF_i \times F)$$

### Basis

$$Basis = P_{CTD} - CF_{CTD} \times F$$

### DV01

$$DV01_{future} \approx \frac{DV01_{CTD}}{CF_{CTD}}$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import BondFuture
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = BondFuture("BOND-FUTURE-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.USD, "CP-1", bond_coupon=0.06, bond_maturity_years=10.0)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
