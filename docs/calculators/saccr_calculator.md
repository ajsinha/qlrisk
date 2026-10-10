# SA-CCR Calculator Documentation v1.2.0

## Overview

The SA-CCR (Standardised Approach for Counterparty Credit Risk) Calculator implements the Basel III/IV regulatory framework for calculating Exposure at Default (EAD) for derivatives.

## Formula

$$EAD = \alpha \times (RC + PFE)$$

Where:
- $\alpha$ = 1.4 (regulatory multiplier)
- $RC$ = Replacement Cost
- $PFE$ = Potential Future Exposure

## Components

### Replacement Cost (RC)

**Unmargined:**
$$RC = max(V - C, 0)$$

**Margined:**
$$RC = max(V - C, TH + MTA - NICA, 0)$$

Where:
- $V$ = Current MTM value
- $C$ = Collateral
- $TH$ = Threshold
- $MTA$ = Minimum Transfer Amount
- $NICA$ = Net Independent Collateral Amount

### Potential Future Exposure (PFE)

$$PFE = multiplier \times AddOn_{aggregate}$$

$$multiplier = min\left(1, Floor + (1-Floor) \times exp\left(\frac{V-C}{2 \times (1-Floor) \times AddOn}\right)\right)$$

Where Floor = 5%

### Add-Ons by Asset Class

| Asset Class | Supervisory Factor |
|-------------|-------------------|
| Interest Rate | 0.5% |
| FX | 4% |
| Credit (IG) | 0.38% - 1.06% |
| Credit (HY) | 1.6% - 6% |
| Equity | 32% |
| Commodity | 18% - 40% |

## Class: SACCRCalculator

### Input: SACCRInput

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `netting_set_id` | str | "" | Netting set identifier |
| `trades` | List[Dict] | [] | Trade details |
| `collateral` | float | 0.0 | Posted collateral |
| `variation_margin` | float | 0.0 | Variation margin |
| `threshold` | float | 0.0 | CSA threshold |
| `minimum_transfer_amount` | float | 0.0 | MTA |
| `margin_period_of_risk` | float | 10.0 | MPOR in days |
| `is_margined` | bool | False | Margined flag |

### Trade Attributes

Each trade dict should contain:

| Field | Type | Description |
|-------|------|-------------|
| `asset_class` | str | "interest_rate", "fx", etc. |
| `notional` | float | Notional amount |
| `maturity` | float | Time to maturity (years) |
| `mtm` | float | Current MTM |
| `delta` | float | Delta for options |
| `rating` | str | Credit rating (for credit) |

### Output: SACCRResult

| Field | Type | Description |
|-------|------|-------------|
| `netting_set_id` | str | Netting set identifier |
| `replacement_cost` | float | RC component |
| `pfe_addon` | float | PFE component |
| `multiplier` | float | PFE multiplier |
| `ead` | float | Final EAD |
| `ir_addon` | float | IR add-on |
| `fx_addon` | float | FX add-on |
| `credit_addon` | float | Credit add-on |
| `equity_addon` | float | Equity add-on |
| `commodity_addon` | float | Commodity add-on |
| `alpha` | float | Alpha factor (1.4) |

## Usage Example

```python
from calculator.python import SACCRCalculator, SACCRInput

calculator = SACCRCalculator()

trades = [
    {
        "asset_class": "interest_rate",
        "notional": 100_000_000,
        "maturity": 5.0,
        "mtm": 1_500_000,
        "delta": 1.0
    },
    {
        "asset_class": "fx",
        "notional": 50_000_000,
        "maturity": 1.0,
        "mtm": 500_000,
        "delta": 1.0
    }
]

result = calculator.calculate(SACCRInput(
    netting_set_id="NS-001",
    trades=trades,
    collateral=1_000_000,
    is_margined=True,
    margin_period_of_risk=10
))

print(f"Replacement Cost: ${result.replacement_cost:,.2f}")
print(f"PFE Add-on: ${result.pfe_addon:,.2f}")
print(f"Multiplier: {result.multiplier:.4f}")
print(f"EAD: ${result.ead:,.2f}")
```

## Regulatory References

- **BCBS 279**: The standardised approach for counterparty credit risk
- **CRR II**: EU implementation
- **Basel IV**: Final calibration (2023+)

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
