# Single Stock Future v1.2.0

<!-- generated:implementation -->
> **Implementation:** `SingleStockFuture` is priced by `price_equity_forward` in `products/python/_pricing.py`. Product terms are keyword arguments: `ticker`, `strike` (fair forward), `quantity`, `is_future`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Single Stock Future |
| **Product Class** | Futures |
| **Asset Class** | Equity |
| **Product Type** | SSF |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Futures contract on individual stocks, providing leveraged exposure to single-name equity price movements.

### Key Characteristics

- **Contract Size:** Typically 100 shares
- **Settlement:** Physical or cash
- **Margin:** Lower capital than stock
- **Dividend:** Reflected in pricing

---

## Mathematical Framework

### Forward Price

$$F = S \times e^{(r - q) \times T}$$

Or discrete dividends:

$$F = (S - PV(Dividends)) \times e^{r \times T}$$

---

## SA-CCR Treatment

Single stock futures use 32% SF:

$$AddOn = 32\% \times Delta \times Notional \times MF$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import SingleStockFuture
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = SingleStockFuture("SINGLE-STOCK-FUTURE-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.USD, "CP-1", ticker="SPX")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
