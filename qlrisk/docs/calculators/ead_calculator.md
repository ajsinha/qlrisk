# Exposure at Default (EAD) Calculator

## Overview

The Exposure at Default (EAD) Calculator estimates the total exposure amount at the time of default. For derivatives and off-balance sheet items, EAD includes both current exposure and potential future exposure. EAD is a key component in Expected Loss and regulatory capital calculations.

## Calculation Methods

### 1. Current Exposure Method (CEM)

The traditional regulatory approach for derivatives exposure.

**Formula:**
```
EAD = max(0, MTM) + Add-on

Add-on = Notional × Add-on Factor

where Add-on Factors depend on:
- Product type (IR, FX, Equity, Credit, Commodity)
- Remaining maturity
```

**Regulatory Add-on Factors:**

| Product | ≤1 Year | 1-5 Years | >5 Years |
|---------|---------|-----------|----------|
| Interest Rate | 0.0% | 0.5% | 1.5% |
| FX | 1.0% | 5.0% | 7.5% |
| Equity | 6.0% | 8.0% | 10.0% |
| Credit | 5.0% | 5.0% | 5.0% |
| Commodity | 10.0% | 12.0% | 15.0% |

### 2. Standardized Approach for CCR (SA-CCR)

The newer regulatory approach replacing CEM.

**Formula:**
```
EAD = α × (RC + PFE)

where:
α = 1.4 (regulatory multiplier)
RC = Replacement Cost
PFE = Potential Future Exposure

RC = max(V - C, TH + MTA - NICA, 0)  [for margined]
RC = max(V - C, 0)                   [for unmargined]

V = Current MTM
C = Collateral value
TH = Threshold
MTA = Minimum Transfer Amount
NICA = Net Independent Collateral Amount
```

### 3. Internal Model Method (IMM)

Uses internal VaR-style models for EAD estimation.

**Formula:**
```
EAD = α × Effective EPE × Notional

Effective EPE = Average of Effective EE profile

α = 1.4 (or bank-specific if approved)
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `current_exposure` | float | Yes | Current mark-to-market value |
| `notional` | float | Yes | Notional/principal amount |
| `credit_conversion_factor` | float | No | CCF for off-balance sheet (default 1.0) |
| `add_on_factor` | float | No | Regulatory add-on factor |
| `collateral_value` | float | No | Value of collateral held |
| `collateral_haircut` | float | No | Haircut on collateral |
| `netting_benefit` | float | No | Netting benefit factor (0-1) |
| `margin_period_of_risk` | float | No | MPOR in years (default 10/252) |
| `replacement_cost` | float | No | For SA-CCR: explicit RC |
| `pfe_add_on` | float | No | For SA-CCR: explicit PFE |

## Usage Examples

### Basic EAD Calculation

```python
from qlrisk.calculator import CalculatorFactory

factory = CalculatorFactory()
ead_calc = factory.get_ead_calculator()

# Simple EAD for positive MTM trade
result = ead_calc.calculate({
    "current_exposure": 500_000,  # Current MTM
    "notional": 10_000_000,
    "credit_conversion_factor": 1.0
})
print(f"EAD: ${result.value.ead:,.2f}")
```

### With Collateral

```python
# EAD with collateral offset
result = ead_calc.calculate({
    "current_exposure": 500_000,
    "notional": 10_000_000,
    "collateral_value": 300_000,
    "collateral_haircut": 0.10  # 10% haircut
})

print(f"Gross EAD: ${result.value.gross_exposure:,.2f}")
print(f"Net EAD: ${result.value.net_exposure:,.2f}")
print(f"Collateral-Adjusted EAD: ${result.value.collateral_adjusted:,.2f}")
```

### With Netting

```python
# Portfolio netting benefit
result = ead_calc.calculate({
    "current_exposure": 500_000,
    "notional": 10_000_000,
    "netting_benefit": 0.40  # 40% netting benefit
})
print(f"Netted EAD: ${result.value.ead:,.2f}")
```

## Output Structure

The calculator returns an `EADResult` dataclass:

```python
@dataclass
class EADResult:
    ead: float                    # Final EAD amount
    gross_exposure: float         # Pre-netting exposure
    net_exposure: float           # Post-netting exposure
    collateral_adjusted: float    # After collateral adjustment
    method: str                   # Calculation method used
    components: Dict[str, Any]    # Breakdown details
```

## Credit Conversion Factors (CCF)

For off-balance sheet items:

| Item Type | CCF |
|-----------|-----|
| Direct credit substitutes | 100% |
| Transaction-related contingent items | 50% |
| Short-term self-liquidating trade letters | 20% |
| Undrawn commitments (unconditionally cancellable) | 0% |
| Undrawn commitments (>1 year) | 50% |
| Undrawn commitments (≤1 year) | 20% |

## Regulatory Context

### Basel III SA-CCR
- Effective since 2022
- More risk-sensitive than CEM
- Recognizes margin, netting, hedging

### Basel III IMM
- Requires regulatory approval
- Uses internal EPE models
- Subject to backtesting requirements

## Best Practices

1. **Netting Sets**: Properly define legally enforceable netting sets
2. **Collateral**: Mark collateral to market frequently
3. **Wrong-Way Risk**: Adjust for correlation between exposure and counterparty credit
4. **MPOR**: Use appropriate margin period of risk (10 days standard, 20 days for illiquid)
5. **Model Validation**: Regular backtesting of EAD estimates

## References

1. Basel Committee - SA-CCR Standard
2. Basel Committee - IMM for CCR
3. ISDA Master Agreement (Netting provisions)
4. Credit Support Annex (CSA) Standards

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

