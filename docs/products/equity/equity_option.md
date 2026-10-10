# Equity Option v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Equity Option |
| **Product Class** | Equity Derivatives |
| **Asset Class** | Equity |
| **Product Type** | EQUITY_OPTION |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

An Equity Option gives the holder the right to buy (call) or sell (put) an underlying equity or index at a predetermined strike price.

---

## Mathematical Framework

### Black-Scholes Model

$$Call = S e^{-qT} N(d_1) - K e^{-rT} N(d_2)$$

$$d_1 = \frac{\ln(S/K) + (r - q + 0.5\sigma^2)T}{\sigma\sqrt{T}}$$

### Greeks

| Greek | Description |
|-------|-------------|
| Delta | $e^{-qT} N(d_1)$ |
| Gamma | $\frac{e^{-qT} n(d_1)}{S\sigma\sqrt{T}}$ |
| Vega | $S e^{-qT} \sqrt{T} n(d_1)$ |
| Theta | Time decay |

---

## Implementation Example

```python
from datetime import date
from products.python.equity import EquityOption
from products.base import Currency, MarketData, OptionType

eq_opt = EquityOption(
    trade_id="EQOPT-001",
    trade_date=date(2024, 1, 15),
    expiry_date=date(2024, 7, 15),
    underlying="AAPL",
    strike=180.0,
    notional=1000,  # 1000 shares
    currency=Currency.USD,
    counterparty_id="CPY-001",
    option_type=OptionType.CALL,
    is_long=True,
    volatility=0.25
)

result = eq_opt.price(market_data)
print(f"Premium: ${result.npv:,.2f}")
print(f"Delta: {result.greeks['delta']:.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
