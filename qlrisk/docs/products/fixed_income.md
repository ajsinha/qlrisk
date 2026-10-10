# Fixed Income Products v1.1.0

## Overview

QLRisk provides comprehensive support for fixed income products across all major categories including government bonds, corporate bonds, and asset-backed securities.

---

## Government Bonds

### US Treasury Securities

| Product | Description | Duration | Day Count |
|---------|-------------|----------|-----------|
| **T-Bill** | Zero-coupon, < 1 year | 0-1 year | ACT/360 |
| **T-Note** | Coupon-bearing, 2-10 years | 1.9-8.5 years | ACT/ACT |
| **T-Bond** | Coupon-bearing, > 10 years | 10-18 years | ACT/ACT |
| **TIPS** | Inflation-protected | Variable | ACT/ACT |
| **STRIPS** | Zero-coupon from stripping | Variable | ACT/ACT |

### International Government Bonds

| Product | Country | Coupon Freq | Day Count |
|---------|---------|-------------|-----------|
| **UK Gilts** | United Kingdom | Semi-Annual | ACT/ACT |
| **German Bunds** | Germany | Annual | ACT/ACT |
| **JGBs** | Japan | Semi-Annual | ACT/365 |
| **French OATs** | France | Annual | ACT/ACT |
| **Italian BTPs** | Italy | Semi-Annual | ACT/ACT |

### Usage Example

```python
from products.python.fixed_income import TreasuryNote, UKGilt, TIPS

# Create a 10-year Treasury Note
t_note = TreasuryNote(
    trade_id="TN-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2034, 1, 15),
    face_value=1000000,
    counterparty_id="CPY-001",
    coupon_rate=0.04,  # 4%
    is_long=True
)

# Price the note
result = t_note.price(market_data)
print(f"Dirty Price: ${result.components['dirty_price']:,.2f}")
print(f"YTM: {result.components['ytm']:.2%}")
print(f"Modified Duration: {result.components['modified_duration']:.2f}")

# Calculate CCR exposure
ccr = t_note.calculate_ccr_exposure(market_data)
print(f"Peak Exposure: ${ccr.peak_exposure:,.2f}")
```

---

## Corporate Bonds

### Investment Grade Bonds

Investment grade bonds (rated BBB- or higher) have lower credit spreads and higher recovery rates.

| Rating | Typical Spread | Recovery Rate |
|--------|---------------|---------------|
| AAA | 20 bps | 55% |
| AA | 40 bps | 50% |
| A | 80 bps | 45% |
| BBB | 150 bps | 40% |

### High Yield Bonds

High yield bonds (rated BB+ or lower) offer higher yields but with greater credit risk.

| Rating | Typical Spread | Recovery Rate |
|--------|---------------|---------------|
| BB | 300 bps | 35% |
| B | 500 bps | 30% |
| CCC | 1000 bps | 25% |

### Seniority Levels

| Seniority | Recovery Rate | Priority |
|-----------|---------------|----------|
| Senior Secured | 55% | 1st |
| Senior Unsecured | 40% | 2nd |
| Senior Subordinated | 30% | 3rd |
| Subordinated | 25% | 4th |
| Junior Subordinated | 15% | 5th |

### Usage Example

```python
from products.python.fixed_income import CorporateBond, Seniority

# Create a corporate bond
corp_bond = CorporateBond(
    trade_id="CORP-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2029, 1, 15),
    face_value=5000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    coupon_rate=0.055,  # 5.5%
    issuer_name="ACME Corp",
    credit_rating="BBB",
    seniority=Seniority.SENIOR_UNSECURED,
    sector="technology",
    is_long=True
)

# Price with credit spread
result = corp_bond.price(market_data)
print(f"Credit Spread: {result.components['credit_spread']:.0%}")
print(f"CS01: ${result.greeks['cs01']:,.2f}")
```

---

## Floating Rate Notes (FRNs)

FRNs pay a floating coupon tied to a reference rate plus a spread.

### Key Features

- **Reference Rates:** SOFR, EURIBOR, SONIA, TONA
- **Reset Frequency:** Typically quarterly
- **Duration:** Very low (to next reset)
- **Rate Risk:** Minimal
- **Credit Risk:** Similar to fixed-rate bonds

### Caps and Floors

FRNs may include embedded options:
- **Cap:** Maximum coupon rate
- **Floor:** Minimum coupon rate (often 0%)

### Usage Example

```python
from products.python.fixed_income import FloatingRateNote

frn = FloatingRateNote(
    trade_id="FRN-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2027, 1, 15),
    face_value=10000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    spread=0.0075,  # 75 bps over SOFR
    reference_rate="SOFR",
    reset_frequency=PaymentFrequency.QUARTERLY,
    issuer_name="Bank ABC",
    floor=0.0,  # 0% floor
    is_long=True
)
```

---

## Asset-Backed Securities

### Mortgage-Backed Securities (MBS)

| Type | Description | Prepayment Risk |
|------|-------------|-----------------|
| **Agency Pass-Through** | Issued by FNMA/FHLMC/GNMA | High |
| **Non-Agency MBS** | Private label | High |
| **CMO** | Tranched structure | Varies by tranche |

### Key Metrics

- **Pool Factor:** Current principal / original principal
- **CPR:** Conditional Prepayment Rate (annualized)
- **SMM:** Single Monthly Mortality = 1 - (1-CPR)^(1/12)
- **WAL:** Weighted Average Life

### Other ABS Types

| Type | Collateral | Typical Rating |
|------|------------|----------------|
| **Auto ABS** | Auto loans | AAA-BBB |
| **Credit Card ABS** | Credit card receivables | AAA-BBB |
| **Student Loan ABS** | Student loans | AAA-BBB |
| **Equipment ABS** | Equipment leases | AAA-BBB |

### Structured Credit

| Product | Description |
|---------|-------------|
| **CDO** | Collateralized Debt Obligation |
| **CLO** | Collateralized Loan Obligation |
| **CMBS** | Commercial MBS |

### Usage Example

```python
from products.python.fixed_income import MBS, ABS, CLO

# Create an MBS
mbs = MBS(
    trade_id="MBS-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2020, 1, 1),
    maturity_date=date(2050, 1, 1),
    face_value=5000000,
    counterparty_id="CPY-001",
    coupon_rate=0.035,
    pool_factor=0.85,  # 85% remaining
    cpr=0.08,  # 8% CPR
    is_agency=True,
    agency="FNMA",
    wac=0.04,  # 4% WAC
    wam=340,  # 340 months WAM
    is_long=True
)

# Price with prepayment model
result = mbs.price(market_data)
print(f"WAL: {result.components['wal']:.2f} years")
print(f"CPR: {result.components['cpr']:.1%}")
```

---

## Pricing Methodology

### Clean vs Dirty Price

```
Dirty Price = Clean Price + Accrued Interest
```

### Yield Calculations

**Yield to Maturity (YTM):**
```
P = Σ (C / (1+y)^t) + (F / (1+y)^n)
```

Where:
- P = Dirty price
- C = Coupon payment
- F = Face value
- y = YTM (semi-annual)
- n = Number of periods

### Duration & Convexity

**Macaulay Duration:**
```
D_mac = Σ (t × PV(CF_t)) / P
```

**Modified Duration:**
```
D_mod = D_mac / (1 + y/f)
```

Where f = frequency

**Convexity:**
```
C = Σ (t² × PV(CF_t)) / P
```

**Price Change Approximation:**
```
ΔP/P ≈ -D_mod × Δy + 0.5 × C × (Δy)²
```

---

## Risk Metrics

### DV01 (Dollar Duration)

```
DV01 = Modified Duration × Price × 0.0001
```

### CS01 (Credit Spread Sensitivity)

```
CS01 = Duration × Price × 0.0001 (for 1bp spread change)
```

### Greeks

| Greek | Description | Formula |
|-------|-------------|---------|
| **DV01** | Interest rate sensitivity | D_mod × P × 0.0001 |
| **CS01** | Credit spread sensitivity | D × P × 0.0001 |
| **Convexity** | Second-order rate sensitivity | Σ(t² × PV) / P |

---

## SA-CCR Treatment

### Interest Rate Add-On

```
AddOn(IR) = SF × d × EffectiveNotional × MF
```

Where:
- SF = 0.50% for interest rate
- d = delta (±1 for linear)
- EffectiveNotional = Notional × Duration
- MF = √(min(M, 1))

### Credit Add-On

For corporate bonds:
```
AddOn(Credit) = SF(rating) × d × Notional × MF
```

SF varies by rating (0.38% for AAA to 6.00% for CCC).

---

## Implementation Classes

| Class | Product Type | Key Features |
|-------|--------------|--------------|
| `TreasuryBill` | T-Bill | Zero coupon, discount |
| `TreasuryNote` | T-Note | Semi-annual coupon |
| `TreasuryBond` | T-Bond | Semi-annual coupon |
| `TIPS` | Inflation-linked | CPI adjustment |
| `UKGilt` | UK Gilt | GBP, semi-annual |
| `GermanBund` | Bund | EUR, annual |
| `JGB` | Japanese GB | JPY, semi-annual |
| `CorporateBond` | Corporate | Credit spread |
| `FloatingRateNote` | FRN | Floating coupon |
| `ConvertibleBond` | Convertible | Equity option |
| `MBS` | Mortgage-backed | Prepayment |
| `ABS` | Asset-backed | Various collateral |
| `CDO` | CDO | Tranched |
| `CLO` | CLO | Leveraged loans |

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
