# Mortgage-Backed Securities (MBS) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Mortgage-Backed Securities (MBS) |
| **Product Class** | Fixed Income - Securitized Products |
| **Asset Class** | Interest Rate |
| **Product Type** | MBS |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Mortgage-Backed Securities are bonds secured by a pool of residential mortgages. Cash flows from the underlying mortgages (principal and interest) are passed through to investors. Key risk is prepayment risk—borrowers can refinance when rates fall.

### Types of MBS

| Type | Guarantee | Issuer |
|------|-----------|--------|
| **Agency Pass-Through** | Government/GSE | GNMA, FNMA, FHLMC |
| **Non-Agency MBS** | None | Private label |
| **CMO** | Structured tranches | Various |

---

## Mathematical Framework

### Prepayment Models

#### Single Monthly Mortality (SMM)

$$SMM = 1 - (1 - CPR)^{1/12}$$

Where CPR is the Conditional Prepayment Rate (annualized).

#### PSA Model

$$CPR = \min\left(\frac{t}{30}, 1\right) \times 6\%$$

Where $t$ is the age in months. 100 PSA = 6% CPR at month 30.

### Pool Factor

$$PF = \frac{\text{Current Principal}}{\text{Original Principal}}$$

### Weighted Average Life (WAL)

$$WAL = \frac{\sum_{t=1}^{n} t \times P_t}{\sum_{t=1}^{n} P_t}$$

---

## Cash Flow Modeling

Monthly cash flow includes:
1. Scheduled principal
2. Scheduled interest
3. Prepayments

$$CF_t = Interest_t + Scheduled Principal_t + Prepayment_t$$

---

## Key Metrics

| Metric | Description |
|--------|-------------|
| **WAC** | Weighted Average Coupon |
| **WAM** | Weighted Average Maturity |
| **WAL** | Weighted Average Life |
| **WALA** | Weighted Average Loan Age |
| **OAS** | Option-Adjusted Spread |

---

## Option-Adjusted Analysis

### OAS Calculation

$$P = \sum_{\text{paths}} \sum_{t} \frac{E[CF_t]}{(1 + r_t + OAS)^t}$$

### Effective Duration

$$D_{eff} = \frac{P_{-\Delta r} - P_{+\Delta r}}{2 \times P \times \Delta r}$$

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import MBS
from products.base import Currency, MarketData

mbs = MBS(
    trade_id="MBS-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2020, 1, 1),
    maturity_date=date(2050, 1, 1),
    face_value=5000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    coupon_rate=0.035,
    pool_factor=0.85,
    cpr=0.08,  # 8% CPR
    is_agency=True,
    agency="FNMA",
    wac=0.04,
    wam=340,
    is_long=True
)

result = mbs.price(market_data)
print(f"WAL: {result.components['wal']:.2f} years")
print(f"OAS: {result.components['oas']:.0f} bps")
print(f"Effective Duration: {result.greeks['effective_duration']:.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
