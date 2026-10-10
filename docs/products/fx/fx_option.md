# FX Option v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | FX Option (Vanilla) |
| **Product Class** | Foreign Exchange |
| **Asset Class** | FX |
| **Product Type** | FX_OPTION |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

An FX Option gives the holder the right, but not obligation, to exchange currencies at a predetermined rate (strike) on or before expiration. FX options are priced using the Garman-Kohlhagen model.

### Key Characteristics

- **Call/Put:** Right to buy/sell base currency
- **European/American:** Exercise at/before expiry
- **Premium:** Paid upfront in quote currency
- **Settlement:** Physical or cash

---

## Mathematical Framework

### Garman-Kohlhagen Model

$$Call = S \times e^{-r_f T} \times N(d_1) - K \times e^{-r_d T} \times N(d_2)$$

$$Put = K \times e^{-r_d T} \times N(-d_2) - S \times e^{-r_f T} \times N(-d_1)$$

Where:

$$d_1 = \frac{\ln(S/K) + (r_d - r_f + 0.5\sigma^2)T}{\sigma\sqrt{T}}$$

$$d_2 = d_1 - \sigma\sqrt{T}$$

---

## Greeks

| Greek | Description |
|-------|-------------|
| **Delta** | $e^{-r_f T} N(d_1)$ |
| **Gamma** | $\frac{e^{-r_f T} n(d_1)}{S \sigma \sqrt{T}}$ |
| **Vega** | $S e^{-r_f T} \sqrt{T} n(d_1)$ |
| **Theta** | Time decay |
| **Rho** | Sensitivity to interest rates |

---

## Implementation Example

```python
from datetime import date
from products.python.fx import FXOption
from products.base import Currency, MarketData, OptionType

fx_opt = FXOption(
    trade_id="FXOPT-001",
    trade_date=date(2024, 1, 15),
    expiry_date=date(2024, 7, 15),
    settlement_date=date(2024, 7, 17),
    base_currency=Currency.EUR,
    quote_currency=Currency.USD,
    base_notional=10000000,
    strike=1.10,
    counterparty_id="CPY-001",
    option_type=OptionType.CALL,
    is_long=True,
    volatility=0.08
)

result = fx_opt.price(market_data)
print(f"Premium: ${result.npv:,.2f}")
print(f"Delta: {result.greeks['delta']:.4f}")
print(f"Vega: ${result.greeks['vega']:,.2f}")
```

---

## QuantLib Implementation

```python
from products.qlib.fx import FXOptionQL

fx_opt_ql = FXOptionQL(
    trade_id="FXOPT-QL-001",
    trade_date=date(2024, 1, 15),
    expiry_date=date(2024, 7, 15),
    settlement_date=date(2024, 7, 17),
    base_currency=Currency.EUR,
    quote_currency=Currency.USD,
    base_notional=10000000,
    strike=1.10,
    counterparty_id="CPY-001",
    option_type=OptionType.CALL,
    is_long=True
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
