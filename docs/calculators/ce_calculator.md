# Current Exposure (CE) Calculator

## Overview

The Current Exposure (CE) Calculator determines the immediate credit exposure to a counterparty, representing the loss that would occur if the counterparty defaulted today. CE equals the positive mark-to-market value of derivatives after accounting for netting and collateral.

## Core Formulas

### Gross Current Exposure
```
Gross CE = max(0, MTM)

where MTM = Mark-to-Market value of the position
```

### Net Current Exposure (with netting)
```
Net CE = max(0, Σ MTMᵢ)

where i ∈ netting set
```

### Collateralized Current Exposure
```
Collateralized CE = max(0, Net CE - Effective Collateral)

Effective Collateral = Collateral Held × (1 - Haircut) - Collateral Posted
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mark_to_market` | float | Yes | Current MTM value |
| `collateral_held` | float | No | Collateral received from counterparty |
| `collateral_posted` | float | No | Collateral posted to counterparty |
| `collateral_haircut` | float | No | Haircut percentage on collateral |
| `threshold` | float | No | CSA threshold amount |
| `minimum_transfer_amount` | float | No | MTA under CSA |
| `independent_amount` | float | No | Initial margin / IA |
| `netting_set_id` | str | No | Identifier for netting set |
| `trades_in_netting_set` | List[float] | No | MTM values of all trades in set |

## Usage Examples

### Simple Current Exposure

```python
from qlrisk.calculator import CalculatorFactory

factory = CalculatorFactory()
ce_calc = factory.get_ce_calculator()

# Positive MTM trade
result = ce_calc.calculate({
    "mark_to_market": 500_000
})

print(f"Current Exposure: ${result.value.net_ce:,.2f}")
# Output: Current Exposure: $500,000.00

# Negative MTM trade (zero exposure)
result = ce_calc.calculate({
    "mark_to_market": -200_000
})
print(f"Current Exposure: ${result.value.net_ce:,.2f}")
# Output: Current Exposure: $0.00
```

### With Collateral

```python
# Trade with collateral arrangement
result = ce_calc.calculate({
    "mark_to_market": 500_000,
    "collateral_held": 300_000,
    "collateral_haircut": 0.05  # 5% haircut
})

print(f"Gross CE: ${result.value.gross_ce:,.2f}")
print(f"Collateralized CE: ${result.value.collateralized_ce:,.2f}")
# Effective collateral = 300,000 × 0.95 = 285,000
# Collateralized CE = 500,000 - 285,000 = 215,000
```

### Portfolio Netting

```python
# Netting set with multiple trades
result = ce_calc.calculate({
    "mark_to_market": 500_000,  # Net MTM of primary trade
    "trades_in_netting_set": [500_000, -200_000, 100_000, -150_000],
    "netting_set_id": "NS-001"
})

# Net MTM = 500,000 - 200,000 + 100,000 - 150,000 = 250,000
print(f"Netted CE: ${result.value.net_ce:,.2f}")
```

### With CSA Terms

```python
# Full CSA arrangement
result = ce_calc.calculate({
    "mark_to_market": 500_000,
    "collateral_held": 400_000,
    "threshold": 50_000,          # No collateral call below 50k
    "minimum_transfer_amount": 10_000,
    "independent_amount": 100_000  # Initial margin requirement
})

print(f"Exposure after CSA: ${result.value.collateralized_ce:,.2f}")
```

## Output Structure

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class CEResult:
    """Result of Current Exposure calculation."""
    gross_ce: float
    net_ce: float
    collateralized_ce: float
    exposure_type: str  # 'positive', 'negative', 'zero'
    components: Dict[str, float]
```

## CE vs Other Exposure Metrics

| Metric | Time Horizon | Description |
|--------|--------------|-------------|
| CE | Today | Current mark-to-market |
| EE | Future (expected) | Average future exposure |
| PFE | Future (tail) | High percentile future exposure |
| EPE | Average over life | Effective Positive Exposure |
| EAD | Default point | Exposure used for capital |

## Netting Considerations

### Close-out Netting
- Requires enforceable ISDA Master Agreement
- All trades with counterparty net to single amount
- Reduces gross exposure significantly

### Netting Benefit Calculation
```
Netting Benefit = 1 - (Net CE / Gross CE)

where:
Gross CE = Σ max(0, MTMᵢ)
Net CE = max(0, Σ MTMᵢ)
```

Typical netting benefits range from 40-70% for diversified portfolios.

## Collateral Considerations

### CSA Mechanics
1. Mark positions to market daily
2. Calculate exposure vs threshold
3. Issue margin call if exposure > threshold + MTA
4. Post/receive collateral within settlement period

### Haircuts by Collateral Type
| Type | Standard Haircut |
|------|------------------|
| Cash (same currency) | 0% |
| Cash (different currency) | 8% |
| Government Bonds (0-1yr) | 0.5% |
| Government Bonds (1-5yr) | 2% |
| Government Bonds (>5yr) | 4% |
| Corporate Bonds (IG) | 10% |
| Equities | 25% |

## Regulatory Context

### Basel III
- CE is base for current exposure method
- Used in SA-CCR replacement cost calculation
- Netting recognized with valid netting agreements

### EMIR/Dodd-Frank
- Daily variation margin required for cleared trades
- Initial margin required for uncleared derivatives

## Best Practices

1. **Daily Valuation**: Mark all positions to market daily
2. **Netting Review**: Ensure netting agreements are enforceable
3. **Collateral Management**: Track collateral positions in real-time
4. **Dispute Resolution**: Have process for valuation disputes
5. **Wrong-Way Risk**: Monitor correlation with counterparty credit

## References

1. ISDA Master Agreement Documentation
2. Credit Support Annex (CSA) Templates
3. Basel Committee - SA-CCR Framework
4. BCBS 261 - Margin Requirements

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

