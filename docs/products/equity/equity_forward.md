# Equity Forward v1.2.0

<!-- generated:implementation -->
> **Implementation:** `EquityForward` is priced by `price_equity_forward` in `products/python/_pricing.py`. Product terms are keyword arguments: `ticker`, `strike` (fair forward), `quantity`, `is_future`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Equity Forward |
| **Product Class** | Equity Derivatives |
| **Asset Class** | Equity |
| **Product Type** | EQUITY_FORWARD |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

An Equity Forward is a contract to buy or sell an equity or index at a future date at a predetermined price.

---

## Mathematical Framework

### Forward Price

$$F = S \times e^{(r - q) \times T}$$

### NPV

$$NPV = (F_{market} - F_{contract}) \times e^{-rT} \times N$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import EquityForward
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = EquityForward("EQUITY-FORWARD-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.USD, "CP-1", ticker="SPX")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
