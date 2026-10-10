# Basis Swap

<!-- generated:implementation -->
> **Implementation:** `BasisSwap` has its own pricer and constructor arguments (see the example and `help(qlrisk.products.python.BasisSwap)`).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Basis Swap |
| **Product Class** | Interest Rate Derivatives |
| **Asset Class** | Interest Rate |
| **Product Type** | BASIS_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A basis swap is an interest rate swap where both legs are floating rate, but reference different indices. Common types include tenor basis swaps (3M vs 6M LIBOR) and cross-currency basis swaps.

### Key Characteristics

- **Both Legs Floating:** Two different indices
- **Basis Spread:** Added to one leg to equalize value
- **Uses:** Funding optimization, curve arbitrage

---

## Types of Basis Swaps

| Type | Description |
|------|-------------|
| **Tenor Basis** | Same index, different tenors (3M vs 6M) |
| **Index Basis** | Different indices (SOFR vs Fed Funds) |
| **Cross-Currency** | Different currencies (USD SOFR vs EUR €STR) |

---

## Mathematical Framework

### Basis Swap Rate

The fair basis swap rate $b$ satisfies:

$$\sum_{i=1}^{n} f_1(i) \times \tau_i \times DF(t_i) = \sum_{i=1}^{m} (f_2(j) + b) \times \tau_j \times DF(t_j)$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import BasisSwap
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = BasisSwap("BASIS-1", d0, d0, date(2031, 10, 9), 10_000_000, Currency.USD, "CP-1", spread=0.001)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
