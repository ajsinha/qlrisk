# Collateralized Debt Obligation (CDO)

<!-- generated:implementation -->
> **Implementation:** `CDO` is priced by `price_tranche` in `products/python/_pricing.py`. Product terms are keyword arguments: `pool`, `attachment`, `detachment`, `correlation`, `recovery`, `coupon`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Collateralized Debt Obligation (CDO) |
| **Product Class** | Fixed Income - Structured Credit |
| **Asset Class** | Credit |
| **Product Type** | CDO |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A CDO is a structured financial product that pools together cash flow-generating assets and repackages them into tranches with different risk/return profiles. The collateral can include bonds, loans, or other debt instruments.

### CDO Types

| Type | Collateral |
|------|------------|
| **CBO** | Bonds |
| **CLO** | Leveraged Loans |
| **CFO** | Cash flows |
| **Synthetic CDO** | Credit derivatives |

---

## Tranche Structure

| Tranche | Attachment | Detachment | Rating |
|---------|------------|------------|--------|
| **Super Senior** | 30% | 100% | AAA |
| **Senior** | 15% | 30% | AA/A |
| **Mezzanine** | 7% | 15% | BBB/BB |
| **Junior** | 3% | 7% | B |
| **Equity** | 0% | 3% | NR |

### Loss Allocation

Losses are absorbed starting from equity tranche upward.

---

## Mathematical Framework

### Expected Loss

$$EL = PD \times LGD \times EAD$$

### Tranche Loss

For a tranche with attachment $A$ and detachment $D$:

$$Loss_{tranche} = \max(0, \min(L - A, D - A))$$

### Correlation Impact

Higher default correlation → Higher senior tranche risk

---

## SA-CCR Treatment

CDO tranches require adjusted notional:

$$EN = Notional \times (D - A)$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import CDO
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = CDO("CDO-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", pool="GLOBEX", attachment=0.03, detachment=0.07, correlation=0.30)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
