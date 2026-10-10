# Hedge Fund Interest

<!-- generated:implementation -->
> **Implementation:** `HedgeFundInterest` is priced by `price_cash_equity` in `products/python/_pricing.py`. Product terms are keyword arguments: `ticker` (equity_prices key), `quantity` (default notional / price), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Hedge Fund Interest |
| **Product Class** | Private Markets |
| **Asset Class** | Alternatives - Hedge Funds |
| **Product Type** | HEDGE_FUND |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Hedge fund interests represent investments in pooled investment vehicles that employ various strategies to generate returns. Unlike mutual funds, hedge funds have fewer regulatory constraints and can use leverage, short selling, and derivatives.

### Common Strategies

| Strategy | Description |
|----------|-------------|
| **Long/Short Equity** | Long winners, short losers |
| **Global Macro** | Macro-economic bets |
| **Event Driven** | M&A, restructuring |
| **Relative Value** | Arbitrage opportunities |
| **Quantitative** | Systematic trading |
| **Multi-Strategy** | Combination approach |

### Fee Structure

| Fee | Typical Range |
|-----|---------------|
| Management Fee | 1-2% of AUM |
| Performance Fee | 15-20% of profits |
| Hurdle Rate | 0-8% |
| High Water Mark | Yes (usually) |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import HedgeFundInterest
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = HedgeFundInterest("HEDGE-FUND-INTEREST-1", md.valuation_date, md.valuation_date, date(2099, 10, 9), 5_000_000, Currency.USD, "CP-1", ticker="AAPL")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
