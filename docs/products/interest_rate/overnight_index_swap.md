# Overnight Index Swap (OIS) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Overnight Index Swap (OIS) |
| **Product Class** | Interest Rate Derivatives |
| **Asset Class** | Interest Rate |
| **Product Type** | OIS |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

An Overnight Index Swap is an interest rate swap where the floating leg is tied to an overnight rate index (SOFR, SONIA, €STR, TONA). OIS rates are used to derive risk-free discount curves and measure funding costs.

### Key Characteristics

- **Floating Rate:** Compounded overnight rate
- **Near Risk-Free:** Based on secured overnight rates
- **Benchmark:** Primary curve for discounting
- **Typical Tenors:** 1 week to 30 years

---

## Reference Rates

| Currency | Rate | Description |
|----------|------|-------------|
| USD | SOFR | Secured Overnight Financing Rate |
| EUR | €STR | Euro Short-Term Rate |
| GBP | SONIA | Sterling Overnight Index Average |
| JPY | TONA | Tokyo Overnight Average Rate |

---

## Mathematical Framework

### Compounded Overnight Rate

$$R_{compound} = \prod_{i=1}^{n} (1 + r_i \times d_i) - 1$$

Where:
- $r_i$ = Overnight rate on day $i$
- $d_i$ = Day count fraction (1/360 or 1/365)

### OIS Pricing

Same as standard IRS but floating leg uses compounded overnight rates.

---

## Implementation Example

```python
from datetime import date
from products.python.interest_rate import OvernightIndexSwap
from products.base import Currency, MarketData

ois = OvernightIndexSwap(
    trade_id="OIS-001",
    trade_date=date(2024, 1, 15),
    effective_date=date(2024, 1, 17),
    maturity_date=date(2026, 1, 17),
    notional=100000000,
    fixed_rate=0.045,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    pay_fixed=True,
    overnight_index="SOFR"
)

result = ois.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
