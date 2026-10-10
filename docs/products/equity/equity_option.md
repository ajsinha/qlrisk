# Equity Option v1.2.0

<!-- generated:implementation -->
> **Implementation:** `EquityOption` is priced by `price_equity_option` in `products/python/_pricing.py`. Product terms are keyword arguments: `ticker`, `strike` (ATM), `is_call`, `quantity`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Equity Option |
| **Product Class** | Equity Derivatives |
| **Asset Class** | Equity |
| **Product Type** | EQUITY_OPTION |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

An Equity Option gives the holder the right to buy (call) or sell (put) an underlying equity or index at a predetermined strike price.

---

## Mathematical Framework

### Black-Scholes Model

$$Call = S e^{-qT} N(d_1) - K e^{-rT} N(d_2)$$

$$d_1 = \frac{\ln(S/K) + (r - q + 0.5\sigma^2)T}{\sigma\sqrt{T}}$$

### Greeks

| Greek | Description |
|-------|-------------|
| Delta | $e^{-qT} N(d_1)$ |
| Gamma | $\frac{e^{-qT} n(d_1)}{S\sigma\sqrt{T}}$ |
| Vega | $S e^{-qT} \sqrt{T} n(d_1)$ |
| Theta | Time decay |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import EquityOption
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = EquityOption("EQUITY-OPTION-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.USD, "CP-1", ticker="AAPL", strike=200.0, is_call=True)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
