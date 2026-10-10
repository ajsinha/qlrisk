# Bond (Base Class) v1.2.0

<!-- generated:implementation -->
> **Implementation:** `CorporateBond` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Bond (Generic) |
| **Product Class** | Fixed Income |
| **Asset Class** | Interest Rate |
| **Product Type** | BOND |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

The Bond class is the base implementation for all fixed income products. It provides core functionality for cash flow generation, pricing, duration, and risk calculations that are inherited by specific bond types.

### Core Features

- Cash flow generation
- YTM calculation (Brent's method)
- Duration and convexity
- DV01 and risk metrics
- Accrued interest

---

## Inheritance Hierarchy

```
Bond (Base)
├── TreasuryBill
├── TreasuryNote
├── TreasuryBond
├── TIPS
├── UKGilt
├── GermanBund
├── JGB
├── FrenchOAT
├── MunicipalBond
├── AgencyBond
├── CorporateBond
├── FloatingRateNote
├── ConvertibleBond
├── MBS
├── ABS
├── CDO
└── CLO
```

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import CorporateBond
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = CorporateBond("CORPORATE-BOND-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
