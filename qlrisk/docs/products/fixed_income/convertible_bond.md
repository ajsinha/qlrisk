# Convertible Bond v1.2.0

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
from products.python.fixed_income import ConvertibleBond
from products.base import Currency, MarketData

cb = ConvertibleBond(
    trade_id="CB-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2029, 1, 15),
    face_value=1000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    coupon_rate=0.02,
    issuer_name="Tech Corp",
    underlying_ticker="TECH",
    conversion_ratio=20.0,
    conversion_price=50.0,
    is_long=True
)

# Market data with equity info
market_data.forward_curves["TECH"] = {"spot": 55.0, "div_yield": 0.01}
market_data.volatility_surfaces["TECH_vol"] = 0.35

result = cb.price(market_data)
print(f"Bond Floor: ${result.components['bond_floor']:,.2f}")
print(f"Conversion Value: ${result.components['conversion_value']:,.2f}")
print(f"Conversion Premium: {result.components['conversion_premium']:.1%}")
print(f"Delta: {result.greeks['delta']:.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
