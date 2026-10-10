# Treasury Bill (T-Bill)

<!-- generated:implementation -->
> **Implementation:** `TreasuryBill` is priced by `price_deposit` in `products/python/_pricing.py`. Product terms are keyword arguments: `rate`, `issuer`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
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
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import TreasuryBill
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = TreasuryBill("TREASURY-BILL-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.USD, "CP-1", rate=0.045)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
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
