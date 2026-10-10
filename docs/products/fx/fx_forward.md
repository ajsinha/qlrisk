# FX Forward

<!-- generated:implementation -->
> **Implementation:** `FXForward` has its own pricer and constructor arguments (see the example and `help(qlrisk.products.python.FXForward)`).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | FX Forward |
| **Product Class** | Foreign Exchange |
| **Asset Class** | FX |
| **Product Type** | FX_FORWARD |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

An FX Forward is a contract to exchange currencies at a predetermined rate on a future date. It locks in an exchange rate for future delivery, protecting against currency fluctuations.

### Key Characteristics

- **Settlement:** Physical delivery of currencies
- **Customizable:** Any amount, date, currency pair
- **No Upfront Premium:** Zero NPV at inception
- **Uses:** Hedging, speculation

---

## Mathematical Framework

### Forward Rate (Covered Interest Parity)

$$F = S \times \frac{1 + r_d \times T}{1 + r_f \times T}$$

Or in continuous compounding:

$$F = S \times e^{(r_d - r_f) \times T}$$

Where:
- $S$ = Spot rate
- $r_d$ = Domestic interest rate
- $r_f$ = Foreign interest rate
- $T$ = Time to maturity

### Forward Points

$$Forward Points = (F - S) \times 10000$$

### NPV

$$NPV = N_{base} \times (F_{market} - F_{contract}) \times DF$$

---

## SA-CCR Treatment

$$AddOn_{FX} = SF_{FX} \times Notional \times MF$$

Where $SF_{FX} = 4.0\%$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import FXForward
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = FXForward("FXF-1", d0, date(2027, 10, 9), Currency.EUR, Currency.USD, 1_000_000, 1.10, "CP-1")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

## QuantLib Implementation

```python
from qlrisk.products.qlib.fx import FXForwardQL

fx_fwd_ql = FXForwardQL(
    trade_id="FXFWD-QL-001",
    trade_date=date(2026, 1, 15),
    settlement_date=date(2026, 7, 15),
    base_currency=Currency.EUR,
    quote_currency=Currency.USD,
    base_notional=10000000,
    forward_rate=1.0850,
    counterparty_id="CPY-001",
    is_buy_base=True
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
