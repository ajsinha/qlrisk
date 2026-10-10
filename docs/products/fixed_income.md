# Fixed Income Products
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
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python.fixed_income import TreasuryNote, UKGilt, TIPS

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date

# 10-year Treasury Note, 4% semi-annual coupon (terms are keyword arguments)
t_note = TreasuryNote("TN-001", d0, d0, date(2036, 10, 9), 1_000_000, Currency.USD, "UST", coupon=0.04)
gilt = UKGilt("GILT-001", d0, d0, date(2034, 10, 9), 1_000_000, Currency.GBP, "UKDMO", coupon=0.0425)
tips = TIPS("TIPS-001", d0, d0, date(2031, 10, 9), 1_000_000, Currency.USD, "UST", coupon=0.0125)
for bond in (t_note, gilt, tips):
    print(bond.trade_id, round(bond.price(md).npv, 2))
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
from qlrisk.products.python.fixed_income import CorporateBond

# Corporate bond: discounted at the curve plus the issuer's credit spread (credit_curves["ACME"])
corp_bond = CorporateBond("CORP-001", d0, d0, date(2031, 10, 9), 5_000_000, Currency.USD, "ACME",
                          coupon=0.055, issuer="ACME")
res = corp_bond.price(md)
print(f"NPV {res.npv:,.2f}, credit spread {res.components['credit_spread']:.2%}")
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
from qlrisk.products.python.fixed_income import FloatingRateNote

frn = FloatingRateNote("FRN-001", d0, d0, date(2029, 10, 9), 10_000_000, Currency.USD, "BANK",
                       index="SOFR", spread=0.0075, frequency=4, issuer="GLOBEX")
print(f"FRN NPV: {frn.price(md).npv:,.2f}")
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
from qlrisk.products.python.fixed_income import MBS, ABS, CLO

mbs = MBS("MBS-001", d0, d0, date(2056, 10, 9), 5_000_000, Currency.USD, "AGENCY", coupon=0.055)
abs_note = ABS("ABS-001", d0, d0, date(2031, 10, 9), 5_000_000, Currency.USD, "TRUST", coupon=0.05, cpr=0.12)
clo = CLO("CLO-BBB", d0, d0, date(2033, 10, 9), 5_000_000, Currency.USD, "CLO-MGR", pool="GLOBEX")
for p in (mbs, abs_note, clo):
    r = p.price(md)
    print(p.trade_id, round(r.npv, 2), {k: round(v, 4) for k, v in r.components.items()})
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
