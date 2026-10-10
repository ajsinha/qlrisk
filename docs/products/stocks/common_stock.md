# Common Stock v1.2.0

<!-- generated:implementation -->
> **Implementation:** `CommonStock` is priced by `price_cash_equity` in `products/python/_pricing.py`. Product terms are keyword arguments: `ticker` (equity_prices key), `quantity` (default notional / price), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Common Stock |
| **Product Class** | Equities |
| **Asset Class** | Equity |
| **Product Type** | COMMON_STOCK |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Common stock represents ownership shares in a corporation with voting rights and residual claim on assets. Holders receive dividends (if declared) and benefit from capital appreciation.

### Key Characteristics

- **Voting Rights:** Typically 1 vote per share
- **Dividends:** Variable, at board discretion
- **Residual Claim:** Last in liquidation priority
- **Limited Liability:** Loss limited to investment

---

## Market Cap Categories

| Category | Market Cap | Typical Volatility |
|----------|------------|-------------------|
| Large Cap | >$10B | 15-20% |
| Mid Cap | $2B-$10B | 20-25% |
| Small Cap | $300M-$2B | 25-35% |
| Micro Cap | <$300M | 35-50% |

---

## SA-CCR Treatment

| Type | Supervisory Factor |
|------|-------------------|
| Single Stock | 32% |
| Index | 20% |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import CommonStock
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = CommonStock("COMMON-STOCK-1", md.valuation_date, md.valuation_date, date(2099, 10, 9), 5_000_000, Currency.USD, "CP-1", ticker="AAPL")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
