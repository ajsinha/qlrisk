# Exchange-Traded Fund (ETF)

<!-- generated:implementation -->
> **Implementation:** `ETF` is priced by `price_cash_equity` in `products/python/_pricing.py`. Product terms are keyword arguments: `ticker` (equity_prices key), `quantity` (default notional / price), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Exchange-Traded Fund |
| **Product Class** | Equities - Funds |
| **Asset Class** | Equity |
| **Product Type** | ETF |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

ETFs are investment funds traded on stock exchanges that hold assets like stocks, bonds, or commodities. They combine diversification of mutual funds with intraday trading of stocks.

### ETF Types

| Type | Description | Examples |
|------|-------------|----------|
| Index | Track market indices | SPY, QQQ |
| Sector | Focus on industries | XLF, XLE |
| Leveraged | 2x or 3x returns | TQQQ, SOXL |
| Inverse | Short exposure | SH, SQQQ |
| Thematic | Specific themes | ARKK, BOTZ |

---

## SA-CCR Treatment

ETFs typically use index SF (20%) unless concentrated.

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import ETF
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = ETF("ETF-1", md.valuation_date, md.valuation_date, date(2099, 10, 9), 5_000_000, Currency.USD, "CP-1", ticker="AAPL")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
