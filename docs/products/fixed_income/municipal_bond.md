# Municipal Bond v1.2.0

<!-- generated:implementation -->
> **Implementation:** `MunicipalBond` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Municipal Bond (Muni) |
| **Product Class** | Fixed Income - Municipal Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | MUNICIPAL_BOND |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Municipal bonds are debt securities issued by states, cities, counties, and other governmental entities to fund public projects. A key feature is that interest income is typically exempt from federal income tax and may also be exempt from state and local taxes.

### Key Characteristics

- **Issuers:** States, cities, counties, school districts, public utilities
- **Tax Status:** Generally tax-exempt (federal)
- **Types:** General Obligation (GO) vs. Revenue bonds
- **Coupon:** Fixed or variable
- **Credit Enhancement:** Bond insurance, letters of credit

---

## Municipal Bond Types

| Type | Backing |
|------|---------|
| **General Obligation (GO)** | Full faith and credit, taxing power |
| **Revenue Bonds** | Specific project revenues |
| **Special Tax Bonds** | Dedicated tax revenues |
| **Build America Bonds** | Taxable with federal subsidy |

---

## Tax-Equivalent Yield

For comparison with taxable bonds:

$$y_{TE} = \frac{y_{muni}}{1 - t}$$

Where:
- $y_{muni}$ = Municipal bond yield
- $t$ = Marginal tax rate

---

## Credit Analysis

| Factor | GO Bonds | Revenue Bonds |
|--------|----------|---------------|
| Primary | Tax base, economic conditions | Project revenue, coverage ratio |
| Secondary | Debt burden, fund balance | Reserve funds, rate covenants |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import MunicipalBond
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = MunicipalBond("MUNICIPAL-BOND-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
