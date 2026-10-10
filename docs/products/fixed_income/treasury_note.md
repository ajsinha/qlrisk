# Treasury Note (T-Note) v1.2.0

<!-- legacy-examples -->
> ⚠️ **Some code samples on this page predate v2.0 and no longer match the API** (1 of 1 fail). Use the [user guides](../../guides/README.md), whose examples are executed by the test suite, until this page is revised.
<!-- /legacy-examples -->

<!-- generated:implementation -->
> **Implementation:** `TreasuryNote` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

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
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import TreasuryNote
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = TreasuryNote("TREASURY-NOTE-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

## QuantLib Implementation

```python
from qlrisk.products.qlib.fixed_income import FixedRateBondQL

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
