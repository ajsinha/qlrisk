# Asset-Backed Securities (ABS)

<!-- generated:implementation -->
> **Implementation:** `ABS` is priced by `price_abs` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `cpr`, `issuer` / `spread`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Asset-Backed Securities (ABS) |
| **Product Class** | Fixed Income - Securitized Products |
| **Asset Class** | Interest Rate |
| **Product Type** | ABS |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Asset-Backed Securities are bonds backed by pools of assets other than mortgages. Common collateral includes auto loans, credit card receivables, student loans, and equipment leases. The cash flows from these assets support the bond payments.

### Common ABS Types

| Collateral | Typical Maturity | Prepayment Risk |
|------------|------------------|-----------------|
| **Auto Loans** | 2-5 years | Moderate |
| **Credit Cards** | Revolving | Low |
| **Student Loans** | 10-25 years | Moderate |
| **Equipment Leases** | 3-7 years | Low |

---

## Structure

ABS typically have tranched structures:

| Tranche | Rating | Priority |
|---------|--------|----------|
| Class A | AAA | Senior |
| Class B | AA/A | Mezzanine |
| Class C | BBB | Junior |
| Residual | NR | Equity |

### Credit Enhancement

- **Overcollateralization**
- **Subordination**
- **Excess spread**
- **Reserve accounts**

---

## Mathematical Framework

### Waterfall Mechanics

1. Pay senior interest
2. Pay senior principal
3. Pay mezzanine interest
4. Pay mezzanine principal
5. Junior tranches
6. Residual cash flow

### Loss Allocation

Losses are allocated in reverse order of seniority.

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import ABS
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = ABS("ABS-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, cpr=0.10, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
