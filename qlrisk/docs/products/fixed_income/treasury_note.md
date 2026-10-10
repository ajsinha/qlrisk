# Treasury Note (T-Note) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Treasury Note (T-Note) |
| **Product Class** | Fixed Income - Government Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | TREASURY_NOTE |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

A Treasury Note is a marketable U.S. government debt security with a fixed interest rate and maturity between 2 and 10 years. T-Notes pay semi-annual coupon interest and return the principal at maturity. They are the most actively traded U.S. government securities and serve as a benchmark for pricing other fixed-income instruments.

### Key Characteristics

- **Issuer:** U.S. Department of the Treasury
- **Maturity:** 2, 3, 5, 7, or 10 years
- **Coupon:** Fixed, paid semi-annually
- **Day Count Convention:** ACT/ACT (ICMA)
- **Minimum Investment:** $100
- **Benchmark Status:** Primary benchmark for intermediate-term rates

---

## Mathematical Framework

### Clean Price

The clean price (excluding accrued interest) is the present value of all future cash flows:

$$P_{clean} = \sum_{i=1}^{n} \frac{C/2}{(1 + y/2)^i} + \frac{F}{(1 + y/2)^n}$$

Where:
- $C$ = Annual coupon payment ($F \times c$)
- $c$ = Coupon rate
- $F$ = Face value
- $y$ = Yield to maturity (annual, semi-annually compounded)
- $n$ = Number of remaining coupon periods

### Dirty Price (Full Price)

$$P_{dirty} = P_{clean} + AI$$

Where $AI$ is accrued interest:

$$AI = \frac{C}{2} \times \frac{\text{Days since last coupon}}{\text{Days in coupon period}}$$

### Yield to Maturity (YTM)

YTM is the internal rate of return solving:

$$P_{dirty} = \sum_{i=1}^{n} \frac{C/2}{(1 + y/2)^{t_i}} + \frac{F}{(1 + y/2)^{t_n}}$$

Where $t_i$ represents the time (in semi-annual periods) to each cash flow.

---

## Duration & Convexity

### Macaulay Duration

$$D_{Mac} = \frac{\sum_{i=1}^{n} t_i \times \frac{CF_i}{(1 + y/2)^{t_i}}}{P_{dirty}}$$

### Modified Duration

$$D_{Mod} = \frac{D_{Mac}}{1 + y/2}$$

### Convexity

$$C = \frac{1}{P} \sum_{i=1}^{n} \frac{t_i(t_i + 1) \times CF_i}{(1 + y/2)^{t_i + 2}}$$

### Price Change Approximation

$$\frac{\Delta P}{P} \approx -D_{Mod} \times \Delta y + \frac{1}{2} C \times (\Delta y)^2$$

---

## Risk Metrics

### DV01 (Dollar Value of 01)

$$DV01 = \frac{P \times D_{Mod}}{10000}$$

### Key Rate Duration

Sensitivity to specific points on the yield curve:

$$KRD_k = -\frac{1}{P} \times \frac{\partial P}{\partial y_k}$$

---

## CCR Exposure

For T-Notes, the exposure profile follows:

$$EE(t) = \max(0, V_0 + \sigma_{rate} \times D_{Mod} \times V_0 \times \sqrt{t})$$

The Potential Future Exposure (PFE) at confidence level $\alpha$:

$$PFE_\alpha(t) = V_0 \times D_{Mod} \times \sigma_{rate} \times \sqrt{t} \times \Phi^{-1}(\alpha)$$

---

## SA-CCR Treatment

### Effective Notional

$$EN = Notional \times SD$$

Where Supervisory Duration:

$$SD = \frac{e^{-0.05 \times S} - e^{-0.05 \times E}}{0.05}$$

- $S$ = Start date (0 for T-Notes)
- $E$ = End date (maturity)

### Add-On

$$AddOn_{IR} = SF_{IR} \times \delta \times EN \times MF$$

- $SF_{IR} = 0.50\%$
- $\delta = 1$ (long) or $-1$ (short)

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import TreasuryNote
from products.base import Currency, MarketData, PaymentFrequency

# Create a 10-year Treasury Note
tnote = TreasuryNote(
    trade_id="TNOTE-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2034, 1, 15),
    face_value=10000000,  # $10M face value
    currency=Currency.USD,
    counterparty_id="CPY-001",
    coupon_rate=0.04,  # 4% coupon
    coupon_frequency=PaymentFrequency.SEMI_ANNUAL,
    is_long=True
)

# Create market data
market_data = MarketData(
    valuation_date=date(2024, 6, 15),
    discount_curve={
        0.5: 0.045, 1.0: 0.046, 2.0: 0.047,
        5.0: 0.048, 10.0: 0.050
    }
)

# Price the T-Note
result = tnote.price(market_data)

print(f"Clean Price: {result.components['clean_price']:.4f}")
print(f"Dirty Price: {result.components['dirty_price']:.4f}")
print(f"Accrued Interest: ${result.components['accrued_interest']:,.2f}")
print(f"YTM: {result.components['ytm']:.2%}")
print(f"Modified Duration: {result.components['modified_duration']:.2f}")
print(f"Convexity: {result.components['convexity']:.2f}")
print(f"DV01: ${result.greeks['dv01']:,.2f}")

# Calculate SA-CCR
saccr = tnote.calculate_saccr(market_data)
print(f"EAD: ${saccr.ead:,.2f}")
```

---

## QuantLib Implementation

```python
from products.qlib.fixed_income import FixedRateBondQL

# Use QuantLib for enhanced accuracy
tnote_ql = FixedRateBondQL(
    trade_id="TNOTE-QL-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2034, 1, 15),
    face_value=10000000,
    coupon_rate=0.04,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    settlement_days=1
)

# QuantLib provides exact pricing with proper conventions
result_ql = tnote_ql.price(market_data)
```

---

## Market Conventions

| Convention | Value |
|------------|-------|
| Quotation | Price (points and 32nds) |
| Settlement | T+1 |
| Day Count | ACT/ACT (ICMA) |
| Coupon Frequency | Semi-annual |
| Business Days | US Government Securities |

---

## Regulatory Treatment

- **Basel III Risk Weight:** 0% (sovereign)
- **LCR Classification:** HQLA Level 1
- **CVA Exemption:** Yes (government bonds)

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
