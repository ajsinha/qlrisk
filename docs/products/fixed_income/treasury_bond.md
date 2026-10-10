# Treasury Bond (T-Bond) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Treasury Bond (T-Bond) |
| **Product Class** | Fixed Income - Government Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | TREASURY_BOND |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

Treasury Bonds are long-term U.S. government debt securities with maturities greater than 10 years, typically issued with 20 or 30-year terms. They pay semi-annual fixed coupon interest and are considered one of the safest investments globally due to the full faith and credit of the U.S. government.

### Key Characteristics

- **Issuer:** U.S. Department of the Treasury
- **Maturity:** 20 or 30 years
- **Coupon:** Fixed, paid semi-annually
- **Day Count:** ACT/ACT (ICMA)
- **Long Duration:** High interest rate sensitivity
- **Benchmark:** Key benchmark for long-term rates

---

## Mathematical Framework

### Present Value

$$P = \sum_{i=1}^{n} \frac{C/2}{(1 + y/2)^i} + \frac{F}{(1 + y/2)^n}$$

### Duration Metrics

For long-dated bonds, duration is significant:

$$D_{Mac} \approx 15-20 \text{ years for 30Y bonds}$$

$$D_{Mod} = \frac{D_{Mac}}{1 + y/2}$$

### High Convexity

Long bonds exhibit significant positive convexity:

$$C = \frac{1}{P(1+y)^2} \sum_{i=1}^{n} t_i(t_i+1) \times CF_i \times e^{-y \times t_i}$$

---

## Risk Characteristics

| Metric | 20Y Bond | 30Y Bond |
|--------|----------|----------|
| Typical Duration | 12-15 years | 17-22 years |
| DV01 per $1M | $1,200-$1,500 | $1,700-$2,200 |
| Convexity | 180-250 | 350-500 |

---

## SA-CCR Treatment

Due to long duration:

$$EN = Notional \times SD_{30Y}$$

Where $SD_{30Y} \approx 14.8$ (for 30-year maturity)

$$AddOn = 0.50\% \times 14.8 \times Notional \times MF$$

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import TreasuryBond
from products.base import Currency, MarketData

# Create a 30-year Treasury Bond
tbond = TreasuryBond(
    trade_id="TBOND-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2054, 1, 15),
    face_value=5000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    coupon_rate=0.0425,  # 4.25% coupon
    is_long=True
)

result = tbond.price(market_data)
print(f"Duration: {result.components['modified_duration']:.2f} years")
print(f"DV01: ${result.greeks['dv01']:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
