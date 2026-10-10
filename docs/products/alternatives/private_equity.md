# Private Equity Interest

<!-- generated:implementation -->
> **Implementation:** `PrivateEquityInterest` is priced by `price_cash_equity` in `products/python/_pricing.py`. Product terms are keyword arguments: `ticker` (equity_prices key), `quantity` (default notional / price), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Private Equity Interest |
| **Product Class** | Private Markets |
| **Asset Class** | Alternatives - Private Equity |
| **Product Type** | PRIVATE_EQUITY |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Private equity interests represent ownership stakes in private companies or private equity funds. These are illiquid investments with long holding periods and irregular valuations.

### PE Fund Types

| Type | Strategy |
|------|----------|
| **Buyout** | Acquire mature companies |
| **Growth** | Minority stakes in growing companies |
| **Venture Capital** | Early-stage investing |
| **Distressed** | Turnaround situations |
| **Secondaries** | Purchase existing LP interests |

### Key Metrics

| Metric | Description |
|--------|-------------|
| **IRR** | Internal Rate of Return |
| **TVPI** | Total Value to Paid-In |
| **DPI** | Distributions to Paid-In |
| **RVPI** | Residual Value to Paid-In |

---

## Valuation

### NAV-Based

$$Value = NAV \times (1 - Illiquidity Discount)$$

### IRR-Based

Solve for IRR:

$$0 = \sum_{t} \frac{CF_t}{(1 + IRR)^t}$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import PrivateEquityInterest
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = PrivateEquityInterest("PRIVATE-EQUITY-INTEREST-1", md.valuation_date, md.valuation_date, date(2099, 10, 9), 5_000_000, Currency.USD, "CP-1", ticker="AAPL")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
