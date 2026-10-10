# Interest Rate Swap (IRS) v1.2.0

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
from products.python.interest_rate import InterestRateSwap
from products.base import Currency, MarketData, PaymentFrequency, DayCountConvention

# Create a 5-year payer swap
irs = InterestRateSwap(
    trade_id="IRS-001",
    trade_date=date(2024, 1, 15),
    effective_date=date(2024, 1, 17),
    maturity_date=date(2029, 1, 17),
    notional=50000000,  # $50M
    fixed_rate=0.04,  # 4%
    currency=Currency.USD,
    counterparty_id="CPY-001",
    pay_fixed=True,
    fixed_frequency=PaymentFrequency.SEMI_ANNUAL,
    float_frequency=PaymentFrequency.QUARTERLY,
    fixed_day_count=DayCountConvention.THIRTY_360,
    float_day_count=DayCountConvention.ACT_360,
    float_index="SOFR"
)

# Market data
market_data = MarketData(
    valuation_date=date(2024, 6, 15),
    discount_curve={
        0.25: 0.048, 0.5: 0.049, 1: 0.050,
        2: 0.051, 5: 0.052, 10: 0.053
    }
)

# Price the swap
result = irs.price(market_data)
print(f"NPV: ${result.npv:,.2f}")
print(f"Fixed Leg PV: ${result.components['fixed_leg_pv']:,.2f}")
print(f"Floating Leg PV: ${result.components['floating_leg_pv']:,.2f}")
print(f"Par Swap Rate: {result.components['par_rate']:.2%}")
print(f"DV01: ${result.greeks['dv01']:,.2f}")

# CCR Exposure
ccr = irs.calculate_ccr_exposure(market_data)
print(f"EPE: ${ccr.epe:,.2f}")
print(f"Peak Exposure: ${ccr.peak_exposure:,.2f}")

# SA-CCR
saccr = irs.calculate_saccr(market_data)
print(f"EAD: ${saccr.ead:,.2f}")
```

---

## QuantLib Implementation

```python
from products.qlib.interest_rate import InterestRateSwapQL

# QuantLib provides:
# - Exact curve bootstrapping
# - Proper day count handling
# - Business day adjustments

irs_ql = InterestRateSwapQL(
    trade_id="IRS-QL-001",
    trade_date=date(2024, 1, 15),
    effective_date=date(2024, 1, 17),
    maturity_date=date(2029, 1, 17),
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
