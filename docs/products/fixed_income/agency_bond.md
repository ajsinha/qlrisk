# Agency Bond v1.2.0

<!-- generated:implementation -->
> **Implementation:** `AgencyBond` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Agency Bond |
| **Product Class** | Fixed Income - Agency Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | AGENCY_BOND |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Agency bonds are debt securities issued by government-sponsored enterprises (GSEs) and federal agencies. While not directly backed by the U.S. government, they carry an implicit government guarantee (for GSEs) or explicit guarantee (for federal agencies).

### Key Issuers

| Agency | Type | Guarantee |
|--------|------|-----------|
| **Fannie Mae (FNMA)** | GSE | Implicit |
| **Freddie Mac (FHLMC)** | GSE | Implicit |
| **Federal Home Loan Banks (FHLB)** | GSE | Implicit |
| **Ginnie Mae (GNMA)** | Federal | Explicit |
| **Tennessee Valley Authority (TVA)** | Federal | Implicit |

---

## Characteristics

- **Spread:** Trade at a small spread to Treasuries
- **Call Features:** Many are callable
- **Step-Up Coupons:** Common structure
- **Liquidity:** Very liquid secondary market

---

## Callable Bond Pricing

For callable agencies:

$$P = P_{bullet} - C_{call}$$

Where $C_{call}$ is the embedded call option value.

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import AgencyBond
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = AgencyBond("AGENCY-BOND-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
