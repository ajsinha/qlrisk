# VIX Future v1.2.0

<!-- generated:implementation -->
> **Implementation status:** `VIXFuture` currently uses **placeholder pricing** (`notional × discount factor × 1%`), so its PV and risk are not meaningful yet. It is on the roadmap for a real model.
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | VIX Future |
| **Product Class** | Futures - Volatility |
| **Asset Class** | Equity |
| **Product Type** | VIX_FUTURE |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Futures on the CBOE Volatility Index (VIX), which measures expected 30-day S&P 500 volatility. Used for volatility trading and portfolio hedging.

### Key Characteristics

- **Settlement:** Cash settled to VIX spot
- **Multiplier:** $1,000 per point
- **Term Structure:** Typically in contango
- **Roll Yield:** Negative (contango) or positive (backwardation)

---

## Mathematical Framework

### VIX Term Structure

Typically upward sloping (contango):

$$VIX_{future} > VIX_{spot}$$

### Roll Cost

$$Roll Cost = \frac{F_{near} - F_{far}}{F_{near}} \times \frac{365}{Days}$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import VIXFuture
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = VIXFuture("VIX-FUTURE-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
