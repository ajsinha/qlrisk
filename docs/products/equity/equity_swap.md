# Equity Swap v1.2.0

<!-- generated:implementation -->
> **Implementation status:** `EquitySwap` currently uses **placeholder pricing** (`notional × discount factor × 1%`), so its PV and risk are not meaningful yet. It is on the roadmap for a real model.
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Equity Swap |
| **Product Class** | Equity Derivatives |
| **Asset Class** | Equity |
| **Product Type** | EQUITY_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

An Equity Swap exchanges the return on an equity or equity index for a fixed or floating interest rate. It provides synthetic equity exposure without direct ownership.

### Key Characteristics

- **Equity Leg:** Total return (price + dividends)
- **Funding Leg:** SOFR + spread
- **No Initial Exchange:** Synthetic position
- **Mark-to-Market:** Periodic resets

---

## Mathematical Framework

### Equity Leg Value

$$V_{equity} = N \times \frac{S_t - S_0}{S_0}$$

### Total Return

$$TR = \frac{S_t - S_0 + Dividends}{S_0}$$

---

## SA-CCR Treatment

$$AddOn = SF_{equity} \times |Delta| \times Notional \times MF$$

Where SF = 32% (single) or 20% (index)

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import EquitySwap
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = EquitySwap("EQUITY-SWAP-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
