# Collateralized Loan Obligation (CLO) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Collateralized Loan Obligation (CLO) |
| **Product Class** | Fixed Income - Structured Credit |
| **Asset Class** | Credit |
| **Product Type** | CLO |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A CLO is a type of CDO backed by a pool of leveraged loans (typically senior secured loans to sub-investment grade companies). CLOs are actively managed by portfolio managers who can trade the underlying loans.

### Key Characteristics

- **Collateral:** Senior secured leveraged loans
- **Active Management:** Manager can reinvest
- **Floating Rate:** Loans typically SOFR-based
- **Reinvestment Period:** Usually 4-5 years
- **Non-Call Period:** Protection for investors

---

## CLO Structure

| Tranche | Spread (bps) | Rating |
|---------|--------------|--------|
| **AAA** | 100-150 | Aaa/AAA |
| **AA** | 175-225 | Aa2/AA |
| **A** | 225-300 | A2/A |
| **BBB** | 350-450 | Baa2/BBB |
| **BB** | 600-800 | Ba2/BB |
| **Equity** | Residual | NR |

---

## Key Metrics

| Metric | Description |
|--------|-------------|
| **WARF** | Weighted Average Rating Factor |
| **WALS** | Weighted Average Life Spread |
| **Diversity Score** | Portfolio concentration |
| **OC Ratio** | Overcollateralization test |
| **IC Ratio** | Interest coverage test |

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import CLO
from products.base import Currency, MarketData

clo = CLO(
    trade_id="CLO-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 1),
    maturity_date=date(2032, 1, 1),
    face_value=10000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    spread=0.015,  # 150 bps
    tranche="AAA",
    pool_notional=400000000,
    reinvestment_end=date(2028, 1, 1),
    is_long=True
)

result = clo.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
