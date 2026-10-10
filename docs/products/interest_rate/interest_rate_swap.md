# Interest Rate Swap (IRS)

<!-- generated:implementation -->
> **Implementation:** `InterestRateSwap` has its own pricer and constructor arguments (see the example and `help(qlrisk.products.python.InterestRateSwap)`).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Interest Rate Swap (IRS) |
| **Product Class** | Interest Rate Derivatives |
| **Asset Class** | Interest Rate |
| **Product Type** | IRS |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

An Interest Rate Swap is an agreement between two parties to exchange interest rate cash flows based on a notional principal. The most common type is a fixed-for-floating swap where one party pays a fixed rate while receiving a floating rate (or vice versa).

### Key Characteristics

- **Notional:** Reference amount (not exchanged)
- **Fixed Leg:** Fixed rate payments
- **Floating Leg:** Variable rate payments (e.g., SOFR)
- **Tenor:** 1 year to 30+ years
- **No Initial Exchange:** Only cash flows are exchanged

---

## Mathematical Framework

### Fixed Leg Present Value

$$PV_{fixed} = N \times c \times \sum_{i=1}^{n} \tau_i \times DF(t_i)$$

Where:
- $N$ = Notional
- $c$ = Fixed rate
- $\tau_i$ = Day count fraction for period $i$
- $DF(t_i)$ = Discount factor to time $t_i$

### Floating Leg Present Value

$$PV_{float} = N \times \sum_{i=1}^{n} f_i \times \tau_i \times DF(t_i)$$

Where $f_i$ is the forward rate for period $i$.

### Swap NPV

For a payer swap (pay fixed, receive float):

$$NPV = PV_{float} - PV_{fixed}$$

### Par Swap Rate

The par swap rate $S$ is the fixed rate that makes NPV = 0:

$$S = \frac{\sum_{i=1}^{n} f_i \times \tau_i \times DF(t_i)}{\sum_{i=1}^{n} \tau_i \times DF(t_i)}$$

---

## Risk Metrics

### DV01 (PV01)

$$DV01 = N \times \sum_{i=1}^{n} \tau_i \times DF(t_i) \times 0.0001$$

### Key Rate Duration

Sensitivity to specific points on the curve:

$$KRD_k = \frac{\partial NPV}{\partial r_k}$$

---

## SA-CCR Treatment

### Effective Notional

$$EN = Notional \times SD$$

Where:

$$SD = \frac{e^{-0.05 \times S} - e^{-0.05 \times E}}{0.05}$$

### Add-On Calculation

$$AddOn_{IR} = SF_{IR} \times \sum_{hedging sets} |HS|$$

Where $SF_{IR} = 0.50\%$

### Hedging Sets

IRS are aggregated by:
1. Currency
2. Maturity bucket (0-1Y, 1-5Y, >5Y)

---

## CCR Exposure

The exposure profile for an IRS follows:

$$EE(t) = \sigma_{rate} \times \sqrt{t} \times N \times D(t) \times \Phi(z_\alpha)$$

Key characteristics:
- Hump-shaped profile
- Peak exposure at ~30% of maturity
- Decreasing exposure toward maturity

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import InterestRateSwap
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = InterestRateSwap("IRS-1", d0, d0, date(2031, 10, 9), 10_000_000, Currency.USD, "CP-1", fixed_rate=0.043)

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
from qlrisk.products.qlib.interest_rate import InterestRateSwapQL

market_data = md  # sample market data from the example above

# QuantLib provides:
# - Exact curve bootstrapping
# - Proper day count handling
# - Business day adjustments

irs_ql = InterestRateSwapQL(
    trade_id="IRS-QL-001",
    trade_date=date(2026, 1, 15),
    effective_date=date(2026, 1, 17),
    maturity_date=date(2031, 1, 17),
    notional=50000000,
    fixed_rate=0.04,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    pay_fixed=True
)

result_ql = irs_ql.price(market_data)
```

---

## Market Conventions

| Currency | Fixed Freq | Float Freq | Fixed DC | Float DC |
|----------|------------|------------|----------|----------|
| USD | Semi-Annual | Quarterly | 30/360 | ACT/360 |
| EUR | Annual | Semi-Annual | 30/360 | ACT/360 |
| GBP | Semi-Annual | Quarterly | ACT/365 | ACT/365 |
| JPY | Semi-Annual | Quarterly | ACT/365 | ACT/365 |

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
