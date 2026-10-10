# QLRisk - Calculator Documentation v2.0.1

<!-- legacy-examples -->
> ⚠️ **Some code samples on this page predate v2.0 and no longer match the API** (5 of 5 fail). Use the [user guides](../guides/README.md), whose examples are executed by the test suite, until this page is revised.
<!-- /legacy-examples -->

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the software it describes are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
```

---

## Overview

QLRisk provides 16 risk calculators, each with dual implementations:
- **Python**: Pure Python implementation using NumPy/SciPy
- **QuantLib**: High-performance implementation using QuantLib-Python

The calculators below cover counterparty credit risk, XVA, credit risk and capital. Market risk adds
`CalculatorType.VAR` and `CalculatorType.EXPECTED_SHORTFALL` (input: `{"pnl": [...], "confidence": 0.99}`
or `{"mean", "std"}` with `method="parametric"`); full portfolio VaR / ES / SVaR runs through
`qlrisk.engine.MarketRiskEngine` — see [../market_risk/var_es.md](../market_risk/var_es.md).

---

## Calculator Summary

| Calculator | Type | Description | Key Methods |
|------------|------|-------------|-------------|
| [PD Calculator](pd_calculator.md) | Credit Risk | Probability of Default | Merton, Rating-based, Hazard rate |
| [LGD Calculator](lgd_calculator.md) | Credit Risk | Loss Given Default | Workout, Market-implied, Regulatory |
| [EAD Calculator](ead_calculator.md) | Credit Risk | Exposure at Default | Current, CCF-based, Regulatory |
| [EL Calculator](el_calculator.md) | Credit Risk | Expected Loss | EL = PD × LGD × EAD |
| [CE Calculator](ce_calculator.md) | Exposure | Current Exposure | Gross, Net (with netting/collateral) |
| [PFE Calculator](pfe_calculator.md) | Exposure | Potential Future Exposure | Monte Carlo, Parametric |
| [EE Calculator](ee_calculator.md) | Exposure | Expected Exposure | Profile, EPE, EEE |
| [CVA Calculator](cva_calculator.md) | XVA | Credit Valuation Adjustment | Unilateral, Bilateral, WWR |
| [DVA Calculator](dva_calculator.md) | XVA | Debit Valuation Adjustment | Own credit adjustment |
| [FVA Calculator](fva_calculator.md) | XVA | Funding Valuation Adjustment | Funding cost/benefit |
| [KVA Calculator](kva_calculator.md) | XVA | Capital Valuation Adjustment | Regulatory capital cost |
| [MVA Calculator](mva_calculator.md) | XVA | Margin Valuation Adjustment | Initial margin cost |
| [EC Calculator](ec_calculator.md) | Capital | Economic Capital | Vasicek, Gordy, Basel IRB |
| [RAROC Calculator](raroc_calculator.md) | Capital | Risk-Adjusted Return | RAROC = (Rev - EL) / EC |
| [IM Calculator](im_calculator.md) | Margin | Initial Margin | ISDA SIMM methodology |
| [SA-CCR Calculator](saccr_calculator.md) | Regulatory | SA-CCR EAD | Basel III/IV compliant |
| [Stress Calculator](stress_calculators.md) | Stress | Stress Testing | Historical, Hypothetical, Reverse |

---

## Usage

### Factory Pattern

```python
from qlrisk.calculator import CalculatorFactory, CalculatorType

# Get factory (singleton)
factory = CalculatorFactory.get_instance()

# Get Python implementation
pd_calc = factory.get_calculator(CalculatorType.PD, implementation='python')

# Get QuantLib implementation (if available)
pd_calc_ql = factory.get_calculator(CalculatorType.PD, implementation='quantlib')

# Calculate
result = pd_calc.calculate({'rating': 'BBB', 'method': 'rating_based'})
print(f"PD: {result.value:.4%}")
```

### Direct Engine Usage

```python
from qlrisk.engine import CCREngine
from qlrisk.calculator import CalculatorType

with CCREngine() as engine:
    result = engine.calculate(CalculatorType.CVA, {
        'ee_profile': [100000, 150000, 200000],
        'time_grid': [0.5, 1.0, 2.0],
        'credit_spread': 0.015,
        'recovery_rate': 0.40
    })
    print(f"CVA: ${result.value:,.2f}")
```

---

## Calculator Categories

### Credit Risk Calculators

Calculate fundamental credit metrics:

| Calculator | Input | Output |
|------------|-------|--------|
| PD | rating, asset_value, debt, volatility | probability (0-1) |
| LGD | seniority, collateral, exposure | loss rate (0-1) |
| EAD | exposure, undrawn, ccf | exposure amount |
| EL | pd, lgd, ead | expected loss amount |

### Exposure Calculators

Calculate exposure metrics for derivatives:

| Calculator | Input | Output |
|------------|-------|--------|
| CE | mtm, collateral | current exposure |
| PFE | mtm, volatility, maturity | PFE at confidence level |
| EE | mtm, notional, maturity | exposure profile |

### XVA Calculators

Calculate valuation adjustments:

| Calculator | Input | Output |
|------------|-------|--------|
| CVA | ee_profile, credit_spread, recovery | CVA amount |
| DVA | nee_profile, own_spread, recovery | DVA amount |
| FVA | exposure_profile, funding_spread | FVA amount |
| KVA | capital_profile, cost_of_capital | KVA amount |
| MVA | im_profile, funding_spread | MVA amount |

### Capital Calculators

Calculate capital requirements:

| Calculator | Input | Output |
|------------|-------|--------|
| EC | exposures, pds, lgds, correlation | economic capital |
| RAROC | revenue, cost, el, ec | RAROC ratio |
| IM | sensitivities, risk_weights | initial margin |
| SA-CCR | trades, collateral, netting | regulatory EAD |

---

## Common Patterns

### Error Handling

```python
from qlrisk.calculator import CalculatorFactory, CalculatorType
from qlrisk.core import CalculationError

factory = CalculatorFactory.get_instance()
calc = factory.get_calculator(CalculatorType.PD)

try:
    result = calc.calculate({'rating': 'INVALID'})
except CalculationError as e:
    print(f"Calculation failed: {e}")
```

### Result Processing

```python
result = calc.calculate(input_data)

# Access result components
value = result.value           # Main result
metadata = result.metadata     # Calculation metadata
details = result.details       # Detailed breakdown
warnings = result.warnings     # Any warnings generated
timestamp = result.timestamp   # Calculation timestamp

# Convert to dictionary
result_dict = result.to_dict()
```

### Batch Processing

```python
from qlrisk.engine import CCREngine, CalculationJob, CalculationTask

with CCREngine() as engine:
    tasks = [
        CalculationTask(
            task_id=f'pd_{rating}',
            calculator_type=CalculatorType.PD,
            input_data={'rating': rating, 'method': 'rating_based'}
        )
        for rating in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B']
    ]
    
    job = CalculationJob(job_id='batch_pd', tasks=tasks, parallel=True)
    result = engine.submit_job(job)
    
    for task_result in result.task_results:
        print(f"{task_result.task_id}: {task_result.result.value:.4%}")
```

---

## Performance Comparison

| Calculator | Python (ms) | QuantLib (ms) | Speedup |
|------------|------------|---------------|---------|
| PD (Merton) | 0.12 | 0.04 | 3.0x |
| CVA (100 pts) | 2.5 | 0.8 | 3.1x |
| PFE (10k paths) | 150 | 45 | 3.3x |
| EC (Vasicek) | 0.8 | 0.3 | 2.7x |

---

## See Also

- [Architecture](../architecture.md) - System design
- [Quickstart](../quickstart.md) - Getting started
- [Mathematical Formulas](../mathematical_formulas.md) - Formula reference
- [SA-CCR](../saccr.md) - SA-CCR methodology

---

*Document Version: 2.0.1*  
*Last Updated: December 2025*  
*Copyright © 2025-2030 Ashutosh Sinha. All Rights Reserved.*
