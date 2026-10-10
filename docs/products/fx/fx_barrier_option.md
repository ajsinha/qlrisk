# FX Barrier Option v1.2.0

<!-- generated:implementation -->
> **Implementation:** `FXBarrierOption` is priced by `price_fx_barrier` in `products/python/_pricing.py`. Product terms are keyword arguments: `pair`, `strike`, `barrier`, `barrier_type` (UpOut/UpIn/DownOut/DownIn), `rebate`, `is_call`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | FX Barrier Option |
| **Product Class** | Foreign Exchange - Exotic |
| **Asset Class** | FX |
| **Product Type** | FX_BARRIER |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A barrier option is an FX option that is activated (knock-in) or deactivated (knock-out) when the underlying spot rate crosses a specified barrier level. Barriers trade at a discount to vanilla options.

### Barrier Types

| Type | Activation |
|------|------------|
| **Up-and-Out** | Knocked out if spot rises above barrier |
| **Up-and-In** | Activated if spot rises above barrier |
| **Down-and-Out** | Knocked out if spot falls below barrier |
| **Down-and-In** | Activated if spot falls below barrier |

---

## Mathematical Framework

### Closed-Form Solutions

For knock-out barriers:

$$BarrierCall = VanillaCall - Rebate \times P(barrier hit)$$

### Monte Carlo

For complex barriers:

$$V = DF \times E[\max(0, S_T - K) \times \mathbb{1}_{no barrier hit}]$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import FXBarrierOption
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = FXBarrierOption("FX-BARRIER-OPTION-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.EUR, "CP-1", pair="EURUSD", strike=1.10, barrier=1.25, barrier_type="UpOut")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
