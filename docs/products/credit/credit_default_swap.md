# Credit Default Swap (CDS)

<!-- generated:implementation -->
> **Implementation:** `CreditDefaultSwap` is priced by `price_cds` in `products/python/_pricing.py`. Product terms are keyword arguments: `reference` (credit curve), `coupon`, `recovery` (0.4), `is_buyer`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Credit Default Swap (CDS) |
| **Product Class** | Credit Derivatives |
| **Asset Class** | Credit |
| **Product Type** | CDS |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Credit Default Swap provides protection against the default of a reference entity. The protection buyer pays periodic premiums; the protection seller pays the loss amount if a credit event occurs.

### Key Characteristics

- **Reference Entity:** Company or sovereign
- **Credit Events:** Bankruptcy, failure to pay, restructuring
- **Premium Leg:** Quarterly spread payments
- **Protection Leg:** Payment upon default
- **Settlement:** Physical or cash (auction)

---

## Mathematical Framework

### CDS Spread

The fair spread $s$ equates premium and protection legs:

$$PV_{premium} = PV_{protection}$$

$$s \times \sum_{i=1}^{n} \tau_i \times DF(t_i) \times S(t_i) = (1-R) \times \sum_{i=1}^{n} DF(t_i) \times [S(t_{i-1}) - S(t_i)]$$

Where:
- $S(t)$ = Survival probability to time $t$
- $R$ = Recovery rate
- $\tau_i$ = Day count fraction

### Hazard Rate Model

$$S(t) = e^{-\lambda t}$$

$$\lambda = \frac{s}{1 - R}$$ (approximate)

---

## SA-CCR Treatment

Credit derivatives use credit supervisory factors:

| Rating | Supervisory Factor |
|--------|--------------------|
| AAA-AA | 0.38% |
| A | 0.42% |
| BBB | 0.54% |
| BB | 1.06% |
| B | 1.06% |
| CCC | 6.00% |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import CreditDefaultSwap
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = CreditDefaultSwap("CREDIT-DEFAULT-SWAP-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", reference="ACME", coupon=0.01)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
