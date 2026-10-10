# Warrant

<!-- generated:implementation -->
> **Implementation:** `Warrant` is priced by `price_equity_option` in `products/python/_pricing.py`. Product terms are keyword arguments: `ticker`, `strike` (ATM), `is_call`, `quantity`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Warrant |
| **Product Class** | Equities - Options |
| **Asset Class** | Equity |
| **Product Type** | WARRANT |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A warrant is a long-term option issued by a company giving the holder the right to buy shares at a specified price. Unlike exchange-traded options, warrants are issued by the company and may result in dilution.

### Key Characteristics

- **Long-term:** Often 5-10+ years
- **Company-issued:** New shares created on exercise
- **Dilution:** Affects existing shareholders
- **Leverage:** Lower cost than shares

---

## Mathematical Framework

### Black-Scholes Adjusted for Dilution

$$W = \frac{1}{1 + \frac{m}{n}} \times BS(S, K, T, r, \sigma)$$

Where m = warrants outstanding, n = shares outstanding

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import Warrant
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = Warrant("WARRANT-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.USD, "CP-1", ticker="AAPL", strike=200.0, is_call=True)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
