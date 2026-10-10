# UK Gilt

<!-- generated:implementation -->
> **Implementation:** `UKGilt` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | UK Gilt (Gilt-Edged Securities) |
| **Product Class** | Fixed Income - Government Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | UK_GILT |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

UK Gilts are bonds issued by the UK Government through the Debt Management Office (DMO). The name "gilt-edged" reflects their historical status as a highly secure investment. Gilts are denominated in GBP and pay semi-annual coupons.

### Key Characteristics

- **Issuer:** UK Government (HM Treasury)
- **Currency:** GBP
- **Coupon Frequency:** Semi-annual
- **Day Count:** ACT/ACT (ICMA)
- **Settlement:** T+1
- **Primary Dealer System:** Gilt-Edged Market Makers (GEMMs)

---

## Types of Gilts

| Type | Description |
|------|-------------|
| **Conventional Gilts** | Fixed coupon, nominal redemption |
| **Index-Linked Gilts** | Inflation-linked (RPI) |
| **Undated Gilts** | Perpetual (largely redeemed) |

---

## Mathematical Framework

Same as standard fixed-rate bonds:

$$P = \sum_{i=1}^{n} \frac{C/2}{(1 + y/2)^i} + \frac{F}{(1 + y/2)^n}$$

### Gilt-Specific Conventions

- Accrued interest: ACT/ACT with ex-dividend period
- Ex-dividend period: 7 business days before coupon

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import UKGilt
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = UKGilt("UK-GILT-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
