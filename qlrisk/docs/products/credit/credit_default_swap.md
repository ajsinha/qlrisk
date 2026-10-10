# Credit Default Swap (CDS) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Credit Default Swap (CDS) |
| **Product Class** | Credit Derivatives |
| **Asset Class** | Credit |
| **Product Type** | CDS |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Credit Default Swap provides protection against the default of a reference entity. The protection buyer pays periodic premiums; the protection seller pays the loss amount if a credit event occurs.

### Key Characteristics

- **Reference Entity:** Company or sovereign
- **Credit Events:** Bankruptcy, failure to pay, restructuring
- **Premium Leg:** Quarterly spread payments
- **Protection Leg:** Payment upon default
- **Settlement:** Physical or cash (auction)

---

## Mathematical Framework

### CDS Spread

The fair spread $s$ equates premium and protection legs:

$$PV_{premium} = PV_{protection}$$

$$s \times \sum_{i=1}^{n} \tau_i \times DF(t_i) \times S(t_i) = (1-R) \times \sum_{i=1}^{n} DF(t_i) \times [S(t_{i-1}) - S(t_i)]$$

Where:
- $S(t)$ = Survival probability to time $t$
- $R$ = Recovery rate
- $\tau_i$ = Day count fraction

### Hazard Rate Model

$$S(t) = e^{-\lambda t}$$

$$\lambda = \frac{s}{1 - R}$$ (approximate)

---

## SA-CCR Treatment

Credit derivatives use credit supervisory factors:

| Rating | Supervisory Factor |
|--------|--------------------|
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
from products.python.credit import CreditDefaultSwap
from products.base import Currency, MarketData

cds = CreditDefaultSwap(
    trade_id="CDS-001",
    trade_date=date(2024, 1, 15),
    effective_date=date(2024, 1, 20),
    maturity_date=date(2029, 3, 20),
    notional=10000000,
    spread=0.01,  # 100 bps
    currency=Currency.USD,
    counterparty_id="CPY-001",
    reference_entity="ACME Corp",
    reference_obligation="Senior Unsecured",
    recovery_rate=0.40,
    is_protection_buyer=True
)

result = cds.price(market_data)
print(f"NPV: ${result.npv:,.2f}")
print(f"Risky PV01: ${result.greeks['risky_pv01']:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
