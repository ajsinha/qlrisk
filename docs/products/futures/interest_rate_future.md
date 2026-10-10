# Interest Rate Future

<!-- generated:implementation -->
> **Implementation:** `InterestRateFuture` is priced by `price_ir_future` in `products/python/_pricing.py`. Product terms are keyword arguments: `index`, `tenor` (0.25), `strike` (traded price), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Interest Rate Future |
| **Product Class** | Futures |
| **Asset Class** | Interest Rate |
| **Product Type** | IR_FUTURE |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Futures on short-term interest rates, used for hedging and speculating on rate movements. Key instruments for curve construction.

### Major IR Futures

| Contract | Reference | Size | Exchange |
|----------|-----------|------|----------|
| SR3 | 3M SOFR | $1M | CME |
| SR1 | 1M SOFR | $5M | CME |
| FF | Fed Funds | $5M | CBOT |

---

## Mathematical Framework

### Price Convention

$$Price = 100 - Rate$$

### DV01

$$DV01 = Notional \times 0.0001 \times \frac{Days}{360}$$

For 3M SOFR: DV01 ≈ $25 per contract per bp

---

## SA-CCR Treatment

$$AddOn = 0.50\% \times Notional \times SD \times MF$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import InterestRateFuture
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = InterestRateFuture("INTEREST-RATE-FUTURE-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.USD, "CP-1", index="SOFR", tenor=0.25)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
