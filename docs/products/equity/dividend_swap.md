# Dividend Swap v1.2.0

<!-- generated:implementation -->
> **Implementation status:** `DividendSwap` currently uses **placeholder pricing** (`notional × discount factor × 1%`), so its PV and risk are not meaningful yet. It is on the roadmap for a real model.
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Dividend Swap |
| **Product Class** | Equity Derivatives |
| **Asset Class** | Equity |
| **Product Type** | DIVIDEND_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Dividend Swap exchanges realized dividends for a fixed payment. It provides pure dividend exposure without equity price risk.

### Key Characteristics

- **Floating Leg:** Actual dividends received
- **Fixed Leg:** Agreed dividend rate
- **Uses:** Dividend hedging, speculation

---

## Mathematical Framework

### Swap Value

$$V = N \times (D_{realized} - D_{strike}) \times DF$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import DividendSwap
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = DividendSwap("DIVIDEND-SWAP-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
