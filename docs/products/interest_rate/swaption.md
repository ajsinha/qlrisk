# Swaption v1.2.0

<!-- generated:implementation -->
> **Implementation:** `Swaption` has its own pricer and constructor arguments (see the example and `help(qlrisk.products.python.Swaption)`).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Swaption (Swap Option) |
| **Product Class** | Interest Rate Derivatives |
| **Asset Class** | Interest Rate |
| **Product Type** | SWAPTION |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

A swaption is an option to enter into an interest rate swap at a future date. A payer swaption gives the right to enter a payer swap (pay fixed); a receiver swaption gives the right to enter a receiver swap (receive fixed).

### Key Characteristics

- **Types:** Payer vs Receiver
- **Exercise:** European, Bermudan, or American
- **Settlement:** Physical or cash
- **Expiry x Tenor:** e.g., 1Y x 5Y = 1-year option into 5-year swap

---

## Mathematical Framework

### Black's Model

$$Swaption = A \times [S \times N(\pm d_1) - K \times N(\pm d_2)]$$

Where:
- $A$ = Annuity factor = $\sum \tau_i \times DF(t_i)$
- $S$ = Forward swap rate
- $K$ = Strike rate
- $+$ for payer, $-$ for receiver

$$d_1 = \frac{\ln(S/K) + 0.5\sigma^2 T}{\sigma\sqrt{T}}$$

### Normal (Bachelier) Model

Alternative for low/negative rates:

$$Swaption = A \times \sigma \sqrt{T} \times [d \times N(d) + n(d)]$$

Where $d = (S - K) / (\sigma \sqrt{T})$

---

## Volatility

| Type | Description |
|------|-------------|
| **Black Vol** | Lognormal, percentage terms |
| **Normal Vol** | Basis points |

Conversion:
$$\sigma_{normal} \approx \sigma_{Black} \times S$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import Swaption
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = Swaption("SWPN-1", d0, date(2027, 10, 9), date(2027, 10, 9), date(2032, 10, 9), 10_000_000, Currency.USD, "CP-1", strike=0.043)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

## QuantLib Implementation

```python
from datetime import date
from qlrisk.products.base import OptionType
from qlrisk.products.qlib.interest_rate import SwaptionQL

market_data = md  # sample market data from the example above

swaption_ql = SwaptionQL(
    trade_id="SWPTN-QL-001",
    trade_date=date(2026, 1, 15),
    option_expiry=date(2027, 1, 15),
    swap_effective=date(2027, 1, 17),
    swap_maturity=date(2032, 1, 17),
    notional=100000000,
    strike=0.04,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    is_payer=True
)

result_ql = swaption_ql.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
