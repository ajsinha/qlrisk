# French OAT (Obligations Assimilables du Trésor)

<!-- generated:implementation -->
> **Implementation:** `FrenchOAT` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | French OAT |
| **Product Class** | Fixed Income - Government Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | FRENCH_OAT |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

French OATs (Obligations Assimilables du Trésor) are medium to long-term French government bonds issued by Agence France Trésor. They are the benchmark securities for French sovereign debt.

### Key Characteristics

- **Issuer:** French Republic (Agence France Trésor)
- **Currency:** EUR
- **Coupon Frequency:** Annual
- **Day Count:** ACT/ACT (ICMA)
- **Maturity:** 2 to 50 years

---

## OAT Types

| Type | Description |
|------|-------------|
| **OAT Standard** | Fixed-rate nominal bonds |
| **OATi** | Inflation-linked (French CPI) |
| **OAT€i** | Inflation-linked (Eurozone HICP) |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import FrenchOAT
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = FrenchOAT("FRENCH-OAT-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
