# Variance Swap v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Variance Swap |
| **Product Class** | Equity Derivatives - Volatility |
| **Asset Class** | Equity |
| **Product Type** | VARIANCE_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Variance Swap is a forward contract on realized variance. It provides pure exposure to volatility without delta hedging requirements.

### Key Characteristics

- **Payoff:** Based on realized vs strike variance
- **Variance Notional:** Per variance point
- **Vega Notional:** Conversion to volatility terms
- **Uses:** Volatility trading, hedging

---

## Mathematical Framework

### Realized Variance

$$\sigma^2_{realized} = \frac{252}{n} \sum_{i=1}^{n} \left(\ln\frac{S_i}{S_{i-1}}\right)^2$$

### Payoff

$$Payoff = N_{var} \times (\sigma^2_{realized} - K_{var})$$

### Vega Notional Conversion

$$N_{vega} = N_{var} \times 2 \times K_{vol}$$

---

## Implementation Example

```python
from datetime import date
from products.python.equity import VarianceSwap
from products.base import Currency, MarketData

var_swap = VarianceSwap(
    trade_id="VARSWP-001",
    trade_date=date(2024, 1, 15),
    effective_date=date(2024, 1, 17),
    maturity_date=date(2024, 7, 17),
    underlying="SPX",
    strike_variance=0.04,  # 20% vol squared
    variance_notional=1000000,  # $1M per variance point
    currency=Currency.USD,
    counterparty_id="CPY-001",
    is_long=True
)

result = var_swap.price(market_data)
print(f"NPV: ${result.npv:,.2f}")
print(f"Fair Variance: {result.components['fair_variance']:.4f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
