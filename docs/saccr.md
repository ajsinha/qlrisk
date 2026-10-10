# SA-CCR Implementation Guide v2.3.1

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the software it describes are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
```

---

## Table of Contents

1. [Overview](#1-overview)
2. [Regulatory Background](#2-regulatory-background)
3. [SA-CCR Formula](#3-sa-ccr-formula)
4. [Replacement Cost](#4-replacement-cost)
5. [PFE Add-On](#5-pfe-add-on)
6. [Asset Class Treatment](#6-asset-class-treatment)
7. [Implementation Details](#7-implementation-details)
8. [Examples](#8-examples)

---

## 1. Overview

The Standardized Approach for Counterparty Credit Risk (SA-CCR) is the Basel III/IV regulatory framework for calculating Exposure at Default (EAD) for derivative transactions. It replaced the Current Exposure Method (CEM) and Standardized Method (SM).

### Key Features

| Feature | Description |
|---------|-------------|
| **Effective Date** | January 1, 2022 (Basel III final) |
| **Scope** | OTC derivatives, exchange-traded derivatives, long settlement transactions |
| **Components** | Replacement Cost (RC) + Potential Future Exposure (PFE) |
| **Alpha Factor** | 1.4 (regulatory multiplier) |

### Formula Summary

$$EAD = \alpha \times (RC + PFE)$$

Where:
- $\alpha = 1.4$ (fixed regulatory multiplier)
- $RC$ = Replacement Cost
- $PFE$ = Potential Future Exposure add-on

---

## 2. Regulatory Background

### Basel Framework References

| Document | Description |
|----------|-------------|
| BCBS 279 | The standardised approach for measuring counterparty credit risk exposures (March 2014) |
| BCBS 424 | Basel III: Finalising post-crisis reforms (December 2017) |
| CRR2/CRD5 | EU implementation of SA-CCR |

### Applicability

SA-CCR applies to:
- OTC derivatives (bilateral)
- Cleared derivatives (with CCP multipliers)
- Exchange-traded derivatives
- Long settlement transactions

---

## 3. SA-CCR Formula

### 3.1 Complete EAD Formula

$$EAD = \alpha \times (RC + PFE)$$

$$\alpha = 1.4$$

### 3.2 For Margined Netting Sets

$$RC = \max(V - C, TH + MTA - NICA, 0)$$

$$PFE = \text{multiplier} \times \text{AddOn}^{aggregate}$$

Where:
- $V$ = Current market value of derivative transactions
- $C$ = Net collateral held (haircut-adjusted)
- $TH$ = Threshold
- $MTA$ = Minimum Transfer Amount
- $NICA$ = Net Independent Collateral Amount

### 3.3 For Unmargined Netting Sets

$$RC = \max(V - C, 0)$$

$$PFE = \text{AddOn}^{aggregate}$$

### 3.4 Multiplier

The multiplier accounts for over-collateralization and negative MTM:

$$\text{multiplier} = \min\left(1, \text{Floor} + (1 - \text{Floor}) \times e^{\frac{V - C}{2 \times (1 - \text{Floor}) \times \text{AddOn}^{aggregate}}}\right)$$

Where Floor = 0.05

---

## 4. Replacement Cost

### 4.1 Unmargined RC

$$RC = \max(V - C, 0)$$

### 4.2 Margined RC

$$RC = \max(V - C, TH + MTA - NICA, 0)$$

### 4.3 Collateral Haircuts

| Collateral Type | Haircut |
|-----------------|---------|
| Cash (same currency) | 0% |
| Cash (different currency) | 8% |
| Government bonds (≤1Y) | 0.5% |
| Government bonds (1-5Y) | 2% |
| Government bonds (>5Y) | 4% |
| Corporate bonds (IG) | 4-12% |
| Equities (main index) | 15% |

---

## 5. PFE Add-On

### 5.1 Aggregate Add-On

$$\text{AddOn}^{aggregate} = \sum_{a} \text{AddOn}_a$$

Where $a$ ∈ {Interest Rate, FX, Credit, Equity, Commodity}

### 5.2 Asset Class Add-Ons

#### Interest Rate

$$\text{AddOn}_{IR} = \sum_{ccy} \sqrt{\sum_{k} D_k^2 + \sum_{k \neq l} \rho_{kl} D_k D_l}$$

Time buckets:
- Bucket 1: < 1 year ($\rho$ = 1.0)
- Bucket 2: 1-5 years ($\rho$ = 0.7 between buckets)
- Bucket 3: > 5 years ($\rho$ = 0.3 between 1 and 3)

#### FX

$$\text{AddOn}_{FX} = \sum_{pair} |d_{pair}| \times SF_{FX}$$

Supervisory Factor: $SF_{FX} = 4\%$

#### Credit

$$\text{AddOn}_{Credit} = \sum_{entity} \sqrt{\sum_k D_k^2 + \sum_{k \neq l} \rho_{kl} D_k D_l}$$

Supervisory Factors:
- AAA-AA: 0.38%
- A: 0.42%
- BBB: 0.54%
- BB: 1.06%
- B: 1.6%
- CCC: 6.0%

#### Equity

$$\text{AddOn}_{Equity} = \sqrt{\sum_{entity} d_{entity}^2 \times \rho^2 + \left(\sum_{entity} d_{entity}\right)^2 \times (1 - \rho^2)}$$

Supervisory Factor: $SF_{Equity} = 32\%$ (single name), $20\%$ (index)
Correlation: $\rho = 50\%$

#### Commodity

$$\text{AddOn}_{Commodity} = \sum_{type} \sqrt{\sum_k D_k^2 + \sum_{k \neq l} \rho D_k D_l}$$

Supervisory Factors:
- Energy: 40%
- Metals: 18%
- Agriculture: 18%
- Other: 18%

---

## 6. Asset Class Treatment

### 6.1 Supervisory Factors

| Asset Class | Sub-Category | SF |
|-------------|--------------|-----|
| Interest Rate | All | 0.5% |
| FX | All | 4.0% |
| Credit (Single) | IG | 0.38-0.54% |
| Credit (Single) | HY | 1.06-6.0% |
| Credit (Index) | IG | 0.38% |
| Credit (Index) | HY | 1.06% |
| Equity (Single) | All | 32% |
| Equity (Index) | All | 20% |
| Commodity | Electricity | 40% |
| Commodity | Oil/Gas | 18% |
| Commodity | Metals | 18% |
| Commodity | Agricultural | 18% |
| Commodity | Other | 18% |

### 6.2 Maturity Factors

$$MF = \sqrt{\frac{\min(M, 1)}{1}}$$ for unmargined

$$MF = \frac{3}{2} \sqrt{\frac{MPOR}{250}}$$ for margined

Where MPOR = Margin Period of Risk (10 business days default)

### 6.3 Delta Adjustments

**Long positions:** $\delta = +1$
**Short positions:** $\delta = -1$
**Options:** $\delta = \phi \times N(\phi \times \frac{\ln(P/K) + 0.5\sigma^2 T}{\sigma\sqrt{T}})$

Where:
- $\phi = +1$ for calls, $-1$ for puts
- $P$ = Underlying price
- $K$ = Strike
- $\sigma$ = Supervisory volatility

---

## 7. Implementation Details

### 7.1 QLRisk Implementation

```python
from qlrisk.calculator import CalculatorFactory, CalculatorType

factory = CalculatorFactory.get_instance()
saccr_calc = factory.get_calculator(CalculatorType.SACCR)

result = saccr_calc.calculate({
    'netting_set_id': 'NS-001',
    'trades': [
        {
            'trade_id': 'IRS-001',
            'asset_class': 'interest_rate',
            'notional': 100_000_000,
            'maturity': 5.0,
            'currency': 'USD',
            'direction': 'pay_fixed',
            'fixed_rate': 0.03,
            'mtm': 500_000
        },
        {
            'trade_id': 'FX-001',
            'asset_class': 'fx',
            'notional': 50_000_000,
            'maturity': 1.0,
            'currency_pair': 'EUR/USD',
            'direction': 'buy',
            'mtm': -100_000
        }
    ],
    'is_margined': True,
    'threshold': 10_000_000,
    'mta': 500_000,
    'collateral': 2_000_000
})

print(f"EAD: ${result.value.ead:,.2f}")
print(f"RC: ${result.value.replacement_cost:,.2f}")
print(f"PFE Add-on: ${result.value.pfe_addon:,.2f}")
print(f"Multiplier: {result.value.multiplier:.4f}")
```

### 7.2 Netting Set Processing

1. Group trades by netting set
2. Calculate net MTM for RC
3. Apply collateral with haircuts
4. Calculate add-ons by asset class
5. Aggregate add-ons
6. Apply multiplier
7. Calculate final EAD

### 7.3 Validation Rules

- Notional must be positive
- Maturity must be non-negative
- Asset class must be valid
- Currency must be valid ISO code
- Trade direction must be specified

---

## 8. Examples

### 8.1 Simple IRS

**Trade:**
- Notional: $100M
- Maturity: 5 years
- Pay fixed 3%, receive floating
- Current MTM: +$500,000

**Calculation:**
```
Adjusted Notional = 100M × SF_IR × MF
                  = 100M × 0.5% × √(min(5,1)/1)
                  = 100M × 0.5% × 1.0
                  = $500,000

RC = max(500,000, 0) = $500,000
PFE = $500,000 (add-on)
EAD = 1.4 × (500,000 + 500,000) = $1,400,000
```

### 8.2 FX Forward Portfolio

**Trades:**
- Buy EUR 50M vs USD @ 1.10, 6M maturity, MTM = +$200,000
- Sell GBP 30M vs USD @ 1.25, 3M maturity, MTM = -$150,000

**Calculation:**
```
Net MTM = 200,000 - 150,000 = $50,000
RC = max(50,000, 0) = $50,000

EUR/USD Add-on = 50M × 4% × √(0.5) = $1,414,214
GBP/USD Add-on = 30M × 1.25 × 4% × √(0.25) = $750,000

Total Add-on = $2,164,214
EAD = 1.4 × (50,000 + 2,164,214) = $3,099,900
```

### 8.3 Margined Netting Set

**Parameters:**
- Net MTM: $1,000,000
- Collateral held: $800,000
- Threshold: $500,000
- MTA: $50,000
- NICA: $0

**Calculation:**
```
RC = max(1,000,000 - 800,000, 500,000 + 50,000 - 0, 0)
   = max(200,000, 550,000, 0)
   = $550,000

Aggregate Add-on = $2,000,000 (assumed)

Multiplier = min(1, 0.05 + 0.95 × exp((1M - 0.8M)/(2 × 0.95 × 2M)))
          = min(1, 0.05 + 0.95 × exp(0.0526))
          = min(1, 1.0)
          = 1.0

PFE = 1.0 × $2,000,000 = $2,000,000
EAD = 1.4 × (550,000 + 2,000,000) = $3,570,000
```

---

## Appendix: Supervisory Parameters

### Correlation Parameters

| Asset Class | Within-Bucket | Cross-Bucket |
|-------------|--------------|--------------|
| Interest Rate | 100% | 30-70% |
| Credit | 80% (IG), 70% (HY) | 50% |
| Equity | 80% (single), 80% (index) | 75% |
| Commodity | 90-99% | 20% |

### Time Bucket Definitions

| Bucket | Interest Rate | Credit | Commodity |
|--------|--------------|--------|-----------|
| 1 | ≤ 1Y | ≤ 1Y | ≤ 1Y |
| 2 | 1-5Y | 1-5Y | 1-5Y |
| 3 | > 5Y | > 5Y | > 5Y |

---

*Document Version: 2.3.1*  
*Last Updated: December 2025*  
*Copyright © 2025-2030 Ashutosh Sinha. All Rights Reserved.*
