# Convertible Bond

<!-- generated:implementation -->
> **Implementation:** `ConvertibleBond` is priced by `price_convertible` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `issuer`, `ticker`, `conversion_ratio`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Convertible Bond |
| **Product Class** | Fixed Income - Hybrid Securities |
| **Asset Class** | Interest Rate / Equity |
| **Product Type** | CONVERTIBLE_BOND |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A convertible bond is a hybrid security that gives the holder the right to convert the bond into a predetermined number of shares of the issuing company's stock. It combines features of both debt and equity instruments.

### Key Characteristics

- **Bond Component:** Fixed or floating coupons
- **Equity Option:** Right to convert to shares
- **Conversion Ratio:** Shares per bond
- **Conversion Price:** Effective stock price at conversion
- **Conversion Premium:** Premium over current stock price

---

## Conversion Terms

### Conversion Ratio

$$CR = \frac{Par}{Conversion Price}$$

### Conversion Value

$$CV = CR \times S$$

Where $S$ is the current stock price.

### Conversion Premium

$$Premium = \frac{P_{bond} - CV}{CV}$$

---

## Mathematical Framework

### Bond Floor

The minimum value assuming no conversion:

$$Bond Floor = \sum_{i=1}^{n} \frac{C}{(1 + r + s)^{t_i}} + \frac{F}{(1 + r + s)^{T}}$$

### Option Value

Using Black-Scholes on the conversion option:

$$Option = CR \times BS(S, K, T, r, \sigma)$$

Where $K = F/CR$ (conversion price).

### Total Value

$$V_{convertible} = Bond Floor + Option Value$$

---

## Greeks

| Greek | Description |
|-------|-------------|
| **Delta** | Sensitivity to stock price |
| **Gamma** | Convexity of delta |
| **Vega** | Sensitivity to volatility |
| **Rho** | Sensitivity to interest rates |
| **Theta** | Time decay |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import ConvertibleBond
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = ConvertibleBond("CONVERTIBLE-BOND-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.02, issuer="ACME", ticker="AAPL")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
