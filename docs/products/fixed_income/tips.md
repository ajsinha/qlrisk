# Treasury Inflation-Protected Securities (TIPS) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | TIPS |
| **Product Class** | Fixed Income - Inflation-Linked Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | TIPS |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Treasury Inflation-Protected Securities (TIPS) are U.S. government bonds designed to protect investors from inflation. The principal value is adjusted based on the Consumer Price Index (CPI), and the fixed coupon rate is applied to the adjusted principal, providing inflation-protected income.

### Key Characteristics

- **Principal Adjustment:** Indexed to CPI-U (non-seasonally adjusted)
- **Real Coupon:** Fixed rate applied to inflation-adjusted principal
- **Deflation Floor:** Principal cannot fall below original face value at maturity
- **Maturities:** 5, 10, and 30 years

---

## Mathematical Framework

### Inflation-Adjusted Principal

$$P_{adj}(t) = P_{0} \times \frac{CPI(t)}{CPI_{base}}$$

Where:
- $P_0$ = Original principal
- $CPI(t)$ = Current CPI
- $CPI_{base}$ = CPI at issue date

### Coupon Payment

$$C(t) = \frac{c}{2} \times P_{adj}(t)$$

### Real Yield

The real yield $r$ satisfies:

$$P_{market} = \sum_{i=1}^{n} \frac{C_i}{(1 + r/2)^i} + \frac{P_{adj}(T)}{(1 + r/2)^n}$$

### Breakeven Inflation

$$i_{BE} = y_{nominal} - y_{real}$$

Where:
- $y_{nominal}$ = Nominal Treasury yield
- $y_{real}$ = TIPS real yield
- $i_{BE}$ = Market-implied inflation expectation

---

## Risk Metrics

### Real Duration

Duration with respect to real yield changes:

$$D_{real} = -\frac{1}{P} \times \frac{\partial P}{\partial r}$$

### Inflation Delta

Sensitivity to inflation expectations:

$$\Delta_{inflation} = \frac{\partial P}{\partial CPI}$$

---

## SA-CCR Treatment

TIPS are treated as interest rate products:

$$AddOn = SF_{IR} \times Notional \times SD \times MF$$

With $SF_{IR} = 0.50\%$

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import TIPS
from products.base import Currency, MarketData

# Create a 10-year TIPS
tips = TIPS(
    trade_id="TIPS-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2034, 1, 15),
    face_value=5000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    real_coupon_rate=0.015,  # 1.5% real coupon
    base_cpi=305.0,
    current_cpi=310.0,
    is_long=True
)

result = tips.price(market_data)
print(f"Adjusted Principal: ${result.components['adjusted_principal']:,.2f}")
print(f"Real Yield: {result.components['real_yield']:.2%}")
print(f"Breakeven Inflation: {result.components['breakeven_inflation']:.2%}")
print(f"Inflation Delta: ${result.greeks['inflation_delta']:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
