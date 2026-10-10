# Corporate Bond

<!-- generated:implementation -->
> **Implementation:** `CorporateBond` is priced by `price_fixed_bond` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `frequency` (2), `issuer` (credit curve), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Corporate Bond |
| **Product Class** | Fixed Income - Corporate Securities |
| **Asset Class** | Interest Rate / Credit |
| **Product Type** | CORPORATE_BOND |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

Corporate bonds are debt securities issued by corporations to raise capital. They offer higher yields than government bonds due to credit risk. The corporate bond market includes investment grade (IG) and high yield (HY) segments.

### Key Characteristics

- **Issuers:** Public and private corporations
- **Credit Risk:** Dependent on issuer's creditworthiness
- **Seniority:** Secured, Senior Unsecured, Subordinated
- **Covenants:** Financial and operational restrictions
- **Recovery:** Expected recovery in default

---

## Credit Rating Scale

| Rating | Category | Spread (bps) |
|--------|----------|--------------|
| AAA | Investment Grade | 20-40 |
| AA | Investment Grade | 40-70 |
| A | Investment Grade | 70-120 |
| BBB | Investment Grade | 120-200 |
| BB | High Yield | 250-400 |
| B | High Yield | 400-600 |
| CCC | High Yield | 600-1000+ |

---

## Mathematical Framework

### Credit Spread

$$s = y_{corp} - y_{rf}$$

Where:
- $y_{corp}$ = Corporate bond yield
- $y_{rf}$ = Risk-free (Treasury) yield

### Risk-Adjusted Pricing

$$P = \sum_{i=1}^{n} \frac{CF_i}{(1 + r_f + s)^{t_i}}$$

### Recovery-Adjusted Spread

$$s = \frac{PD \times LGD}{1 - PD \times LGD}$$

Where:
- $PD$ = Probability of Default
- $LGD$ = Loss Given Default = 1 - Recovery Rate

---

## Seniority and Recovery

| Seniority | Typical Recovery |
|-----------|-----------------|
| Senior Secured | 50-70% |
| Senior Unsecured | 35-50% |
| Senior Subordinated | 25-40% |
| Subordinated | 15-30% |
| Junior Subordinated | 10-20% |

---

## Risk Metrics

### CS01 (Credit Spread Sensitivity)

$$CS01 = D_{spread} \times P \times 0.0001$$

### Spread Duration

$$D_{spread} \approx D_{modified}$$

---

## SA-CCR Treatment

Corporate bonds are treated under credit asset class:

$$AddOn = SF_{credit}(rating) \times Notional \times MF$$

| Rating | SF |
|--------|----|
| AAA-AA | 0.38% |
| A | 0.42% |
| BBB | 0.54% |
| BB | 1.06% |
| B | 1.06% |
| CCC | 6.00% |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import CorporateBond
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = CorporateBond("CORPORATE-BOND-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.05, issuer="ACME")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
