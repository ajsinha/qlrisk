# FX Swap v1.2.0

<!-- generated:implementation -->
> **Implementation:** `FXSwap` has its own pricer and constructor arguments (see the example and `help(qlrisk.products.python.FXSwap)`).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | FX Swap |
| **Product Class** | Foreign Exchange |
| **Asset Class** | FX |
| **Product Type** | FX_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

An FX Swap combines a spot transaction with a forward transaction in opposite directions. It's used to extend or roll forward positions, manage funding, and adjust currency exposure timing.

### Key Characteristics

- **Two Legs:** Near leg (spot) + Far leg (forward)
- **Opposite Directions:** Buy/sell vs sell/buy
- **Same Amount:** Notional unchanged
- **Swap Points:** Difference between spot and forward

---

## Mathematical Framework

### FX Swap Rate

$$Swap Points = F - S = S \times (e^{(r_d - r_f) \times T} - 1)$$

### Net Cost

$$Cost = \frac{Swap Points \times N \times Days}{10000 \times 365}$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import FXSwap
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = FXSwap("FXSW-1", d0, date(2026, 10, 13), date(2027, 10, 9), Currency.EUR, Currency.USD, 1_000_000, 1.085, 1.10, "CP-1")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
