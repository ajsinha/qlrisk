# Credit Linked Note (CLN)

<!-- generated:implementation -->
> **Implementation:** `CreditLinkedNote` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Credit Linked Note (CLN) |
| **Product Class** | Credit Derivatives |
| **Asset Class** | Credit |
| **Product Type** | CLN |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Credit Linked Note is a funded credit derivative combining a bond with an embedded CDS. The investor receives an enhanced yield but loses principal if a credit event occurs on the reference entity.

### Key Characteristics

- **Funded:** Investor provides principal upfront
- **Enhanced Yield:** Credit spread above risk-free
- **Principal at Risk:** Loss upon credit event
- **Uses:** Yield enhancement, credit exposure

---

## Mathematical Framework

### CLN Value

$$CLN = Bond Floor - Embedded CDS$$

### Coupon

$$Coupon = r_{rf} + Credit Spread$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import CreditLinkedNote
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = CreditLinkedNote("CREDIT-LINKED-NOTE-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
