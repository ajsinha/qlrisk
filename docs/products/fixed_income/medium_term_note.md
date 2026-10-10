# Medium Term Note (MTN)

<!-- generated:implementation -->
> **Implementation:** `MediumTermNote` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Medium Term Note (MTN) |
| **Product Class** | Fixed Income - Corporate Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | MEDIUM_TERM_NOTE |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Medium Term Notes are debt instruments issued under a shelf registration program, allowing issuers to offer notes with various maturities, typically ranging from 9 months to 30 years. MTNs provide flexibility in terms of structure and timing.

### Key Characteristics

- **Maturity:** 9 months to 30+ years
- **Shelf Registration:** SEC Rule 415
- **Continuous Offering:** Issued as needed
- **Customizable:** Tailored to investor needs
- **Distribution:** Primary dealer network

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import MediumTermNote
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = MediumTermNote("MEDIUM-TERM-NOTE-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
