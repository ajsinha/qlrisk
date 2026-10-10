# Treasury Inflation-Protected Securities (TIPS)

<!-- generated:implementation -->
> **Implementation:** `TIPS` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

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
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import TIPS
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = TIPS("TIPS-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
