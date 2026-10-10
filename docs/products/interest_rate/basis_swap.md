# Basis Swap v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Basis Swap |
| **Product Class** | Interest Rate Derivatives |
| **Asset Class** | Interest Rate |
| **Product Type** | BASIS_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A basis swap is an interest rate swap where both legs are floating rate, but reference different indices. Common types include tenor basis swaps (3M vs 6M LIBOR) and cross-currency basis swaps.

### Key Characteristics

- **Both Legs Floating:** Two different indices
- **Basis Spread:** Added to one leg to equalize value
- **Uses:** Funding optimization, curve arbitrage

---

## Types of Basis Swaps

| Type | Description |
|------|-------------|
| **Tenor Basis** | Same index, different tenors (3M vs 6M) |
| **Index Basis** | Different indices (SOFR vs Fed Funds) |
| **Cross-Currency** | Different currencies (USD SOFR vs EUR €STR) |

---

## Mathematical Framework

### Basis Swap Rate

The fair basis swap rate $b$ satisfies:

$$\sum_{i=1}^{n} f_1(i) \times \tau_i \times DF(t_i) = \sum_{i=1}^{m} (f_2(j) + b) \times \tau_j \times DF(t_j)$$

---

## Implementation Example

```python
from datetime import date
from products.python.interest_rate import BasisSwap
from products.base import Currency, MarketData

basis = BasisSwap(
    trade_id="BASIS-001",
    trade_date=date(2024, 1, 15),
    effective_date=date(2024, 1, 17),
    maturity_date=date(2029, 1, 17),
    notional=100000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    pay_index="SOFR_3M",
    receive_index="SOFR_6M",
    spread=0.0005  # 5 bps
)

result = basis.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
