# FX Option v1.2.0

<!-- legacy-examples -->
> ⚠️ **Some code samples on this page predate v2.0 and no longer match the API** (1 of 1 fail). Use the [user guides](../../guides/README.md), whose examples are executed by the test suite, until this page is revised.
<!-- /legacy-examples -->

<!-- generated:implementation -->
> **Implementation:** `FXOption` is priced by `price_fx_option` in `products/python/_pricing.py`. Product terms are keyword arguments: `pair`, `strike` (ATMF), `is_call`, `foreign_curve` / `foreign_rate`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | FX Option (Vanilla) |
| **Product Class** | Foreign Exchange |
| **Asset Class** | FX |
| **Product Type** | FX_OPTION |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

An FX Option gives the holder the right, but not obligation, to exchange currencies at a predetermined rate (strike) on or before expiration. FX options are priced using the Garman-Kohlhagen model.

### Key Characteristics

- **Call/Put:** Right to buy/sell base currency
- **European/American:** Exercise at/before expiry
- **Premium:** Paid upfront in quote currency
- **Settlement:** Physical or cash

---

## Mathematical Framework

### Garman-Kohlhagen Model

$$Call = S \times e^{-r_f T} \times N(d_1) - K \times e^{-r_d T} \times N(d_2)$$

$$Put = K \times e^{-r_d T} \times N(-d_2) - S \times e^{-r_f T} \times N(-d_1)$$

Where:

$$d_1 = \frac{\ln(S/K) + (r_d - r_f + 0.5\sigma^2)T}{\sigma\sqrt{T}}$$

$$d_2 = d_1 - \sigma\sqrt{T}$$

---

## Greeks

| Greek | Description |
|-------|-------------|
| **Delta** | $e^{-r_f T} N(d_1)$ |
| **Gamma** | $\frac{e^{-r_f T} n(d_1)}{S \sigma \sqrt{T}}$ |
| **Vega** | $S e^{-r_f T} \sqrt{T} n(d_1)$ |
| **Theta** | Time decay |
| **Rho** | Sensitivity to interest rates |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import FXOption
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = FXOption("FX-OPTION-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.EUR, "CP-1", pair="EURUSD", strike=1.10, is_call=True)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

## QuantLib Implementation

```python
from qlrisk.products.qlib.fx import FXOptionQL

fx_opt_ql = FXOptionQL(
    trade_id="FXOPT-QL-001",
    trade_date=date(2024, 1, 15),
    expiry_date=date(2024, 7, 15),
    settlement_date=date(2024, 7, 17),
    base_currency=Currency.EUR,
    quote_currency=Currency.USD,
    base_notional=10000000,
    strike=1.10,
    counterparty_id="CPY-001",
    option_type=OptionType.CALL,
    is_long=True
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
