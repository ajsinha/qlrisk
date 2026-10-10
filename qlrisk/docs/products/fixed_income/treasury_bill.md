# Treasury Bill (T-Bill) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Treasury Bill (T-Bill) |
| **Product Class** | Fixed Income - Government Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | TREASURY_BILL |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

A Treasury Bill (T-Bill) is a short-term U.S. government debt obligation issued by the U.S. Department of the Treasury with a maturity of one year or less. T-Bills are sold at a discount to face value and do not pay periodic interest (zero-coupon). The investor receives the full face value at maturity, with the difference between the purchase price and face value representing the interest earned.

### Key Characteristics

- **Issuer:** U.S. Department of the Treasury
- **Maturity:** 4, 8, 13, 17, 26, or 52 weeks
- **Coupon:** Zero (sold at discount)
- **Day Count Convention:** ACT/360
- **Minimum Investment:** $100
- **Risk-Free Status:** Considered risk-free for USD-denominated assets
- **Liquidity:** Highly liquid, actively traded in secondary markets

---

## Mathematical Framework

### Discount Pricing

T-Bills are priced on a discount basis. The price is calculated as:

$$P = F \times \left(1 - \frac{d \times t}{360}\right)$$

Where:
- $P$ = Purchase price
- $F$ = Face value
- $d$ = Discount rate (annualized)
- $t$ = Days to maturity

### Bank Discount Yield

The bank discount yield is quoted as:

$$d = \frac{F - P}{F} \times \frac{360}{t}$$

### Money Market Yield (CD Equivalent)

$$y_{MM} = \frac{F - P}{P} \times \frac{360}{t}$$

### Bond Equivalent Yield (BEY)

$$y_{BEY} = \frac{F - P}{P} \times \frac{365}{t}$$

For T-Bills with maturity > 182 days, the BEY calculation uses a more complex formula to account for semi-annual compounding.

### Price from Yield

$$P = \frac{F}{1 + y \times \frac{t}{365}}$$

---

## Risk Metrics

### Duration

For a zero-coupon instrument:

$$D_{Macaulay} = T$$

$$D_{Modified} = \frac{T}{1 + y}$$

Where $T$ is the time to maturity in years.

### DV01 (Dollar Value of 01)

$$DV01 = P \times D_{Modified} \times 0.0001$$

### Convexity

For zero-coupon bonds:

$$C = \frac{T^2}{(1 + y)^2}$$

---

## CCR Exposure

T-Bills have minimal CCR exposure due to:
1. Short maturity (≤ 1 year)
2. Zero coupon (no cash flow risk)
3. Risk-free credit quality

The Expected Exposure (EE) follows a diffusion process:

$$EE(t) = V_0 \times e^{\sigma_{rate} \times \sqrt{t}} \times \left(1 - \frac{t}{T}\right)$$

---

## SA-CCR Treatment

### Supervisory Parameters

| Parameter | Value |
|-----------|-------|
| Asset Class | Interest Rate |
| Supervisory Factor (SF) | 0.50% |
| Supervisory Duration | $SD = \frac{e^{-0.05 \times S} - e^{-0.05 \times E}}{0.05}$ |

### Add-On Calculation

$$AddOn = SF \times \delta \times Notional \times SD \times MF$$

Where:
- $\delta = \pm 1$ (long/short)
- $MF = \sqrt{\min(M, 1)}$ (maturity factor)

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import TreasuryBill
from products.base import Currency, MarketData

# Create a 26-week T-Bill
tbill = TreasuryBill(
    trade_id="TBILL-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2024, 7, 15),
    face_value=1000000,  # $1M face value
    currency=Currency.USD,
    counterparty_id="CPY-001",
    discount_rate=0.0525,  # 5.25% discount rate
    is_long=True
)

# Create market data
market_data = MarketData(
    valuation_date=date(2024, 3, 15),
    discount_curve={0.25: 0.052, 0.5: 0.053, 1.0: 0.054}
)

# Price the T-Bill
result = tbill.price(market_data)

print(f"NPV: ${result.npv:,.2f}")
print(f"Price: ${result.components['price']:,.2f}")
print(f"Discount Yield: {result.components['discount_yield']:.2%}")
print(f"Money Market Yield: {result.components['money_market_yield']:.2%}")
print(f"Bond Equivalent Yield: {result.components['bond_equivalent_yield']:.2%}")

# Calculate CCR exposure
ccr = tbill.calculate_ccr_exposure(market_data)
print(f"Expected Positive Exposure: ${ccr.epe:,.2f}")
print(f"Peak Exposure: ${ccr.peak_exposure:,.2f}")

# Calculate SA-CCR
saccr = tbill.calculate_saccr(market_data)
print(f"Replacement Cost: ${saccr.replacement_cost:,.2f}")
print(f"PFE Add-On: ${saccr.pfe_add_on:,.2f}")
print(f"EAD: ${saccr.ead:,.2f}")
```

---

## Market Conventions

| Convention | Value |
|------------|-------|
| Quotation | Discount rate (%) |
| Settlement | T+1 |
| Day Count | ACT/360 |
| Business Days | US Government Securities |
| Auction | Weekly (4, 8, 13, 26 weeks), Monthly (52 weeks) |

---

## Regulatory Treatment

- **Basel III Risk Weight:** 0% (sovereign)
- **LCR Classification:** HQLA Level 1
- **NSFR Treatment:** 0% RSF

---

## References

1. U.S. Treasury - TreasuryDirect
2. Federal Reserve Bank of New York - Treasury Securities
3. Basel Committee - SA-CCR Framework
4. Hull, J.C. - Options, Futures, and Other Derivatives

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
