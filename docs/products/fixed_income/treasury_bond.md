# Treasury Bond (T-Bond)

<!-- generated:implementation -->
> **Implementation:** `TreasuryBond` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
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
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import TreasuryBond
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = TreasuryBond("TREASURY-BOND-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
