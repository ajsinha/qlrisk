# FX Digital Option

<!-- generated:implementation -->
> **Implementation:** `FXDigitalOption` is priced by `price_fx_digital` in `products/python/_pricing.py`. Product terms are keyword arguments: `pair`, `strike`, `is_call`, `payout`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | FX Digital Option |
| **Product Class** | Foreign Exchange - Exotic |
| **Asset Class** | FX |
| **Product Type** | FX_DIGITAL |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

An FX Digital (Binary) option pays a fixed amount if the underlying spot rate is above (call) or below (put) the strike at expiration. The payoff is all-or-nothing.

### Key Characteristics

- **Fixed Payout:** Predetermined amount
- **Binary Payoff:** 0 or fixed amount
- **High Gamma:** Near strike at expiry
- **Pin Risk:** Risk near strike

---

## Mathematical Framework

### Digital Call

$$Digital_{call} = DF \times Payout \times N(d_2)$$

### Digital Put

$$Digital_{put} = DF \times Payout \times N(-d_2)$$

Where $d_2$ is from Garman-Kohlhagen.

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import FXDigitalOption
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = FXDigitalOption("FX-DIGITAL-OPTION-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.EUR, "CP-1", pair="EURUSD", strike=1.10, payout=100_000)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
