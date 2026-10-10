# Index Future

<!-- generated:implementation -->
> **Implementation:** `IndexFuture` is priced by `price_equity_forward` in `products/python/_pricing.py`. Product terms are keyword arguments: `ticker`, `strike` (fair forward), `quantity`, `is_future`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Index Future |
| **Product Class** | Futures |
| **Asset Class** | Equity |
| **Product Type** | INDEX_FUTURE |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Futures contracts on equity indices providing leveraged exposure to broad market movements. Most liquid derivative instruments globally.

### Major Index Futures

| Contract | Index | Multiplier | Exchange |
|----------|-------|------------|----------|
| ES | S&P 500 | $50 | CME |
| NQ | NASDAQ-100 | $20 | CME |
| YM | Dow Jones | $5 | CBOT |
| RTY | Russell 2000 | $50 | CME |
| FESX | Euro Stoxx 50 | €10 | Eurex |
| NKD | Nikkei 225 | $5 | CME |

---

## Mathematical Framework

### Fair Value

$$F = S \times e^{(r - q) \times T}$$

### Basis

$$Basis = F - S$$

### Cost of Carry

$$COC = S \times (r - q) \times T$$

---

## SA-CCR Treatment

Index futures use equity SF:

$$AddOn = 20\% \times Delta \times Notional \times MF$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import IndexFuture
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = IndexFuture("INDEX-FUTURE-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.USD, "CP-1", ticker="SPX")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
