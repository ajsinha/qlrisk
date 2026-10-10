# QLRisk - Quickstart Guide v2.1.0

<!-- legacy-examples -->
> ⚠️ **Some code samples on this page predate v2.0 and no longer match the API** (11 of 24 fail). Use the [user guides](guides/README.md), whose examples are executed by the test suite, until this page is revised.
<!-- /legacy-examples -->

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the software it describes are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
```

---

## Table of Contents

1. [Installation](#1-installation)
2. [Quick Start](#2-quick-start)
3. [Basic Usage](#3-basic-usage)
4. [Calculator Examples](#4-calculator-examples)
5. [Data Generation](#5-data-generation)
6. [Path Generation](#6-path-generation)
7. [Configuration](#7-configuration)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Installation

### 1.1 Prerequisites

- Python 3.9 or higher
- pip package manager
- (Optional) QuantLib-Python for enhanced performance

### 1.2 Install

```bash
# From source (editable, with dev tools) — installs numpy, scipy and QuantLib
pip install -e ".[dev]"

# Or build a local wheel and install it into any other project/virtualenv
pip install build
python -m build --wheel                       # -> dist/qlrisk-2.1.0-py3-none-any.whl
pip install /path/to/qlrisk/dist/qlrisk-2.1.0-py3-none-any.whl
```

### 1.3 Verify Installation

```bash
python -c "
import qlrisk
print(f'QLRisk v{qlrisk.__version__}')
print(f'Author: {qlrisk.__author__}')
"
```

Expected output:
```
QLRisk v2.1.0
Author: Ashutosh Sinha
```

### 1.4 Run the Demo

```bash
# Quick demonstration (fastest) — `qlrisk` is the installed console script
qlrisk --quick

# Full demonstration
qlrisk

# Performance benchmarks only
qlrisk --benchmark

# Stress testing only
qlrisk --stress

# Alternative: Run as module
python -m qlrisk --quick
```

---

## 2. Quick Start

### 2.1 Minimal Example

```python
from qlrisk.engine import CCREngine
from qlrisk.calculator import CalculatorType

# Create engine with context manager (auto start/stop)
with CCREngine() as engine:
    # Calculate Probability of Default
    result = engine.calculate(
        CalculatorType.PD,
        {'credit_rating': 'BBB'},
        calculator_config={'model': 'transition_matrix'},
    )
    print(f"PD: {result.value:.4%}")
```

### 2.2 Generate Test Data

```python
from qlrisk.data import create_test_dataset

# Create dataset with 500 trades
dataset = create_test_dataset(num_trades=500, seed=42)

print(f"Counterparties: {dataset['summary']['num_counterparties']}")
print(f"Trades: {dataset['summary']['num_trades']}")
print(f"Total Notional: ${dataset['summary']['total_notional']:,.0f}")
print(f"Total MTM: ${dataset['summary']['total_mtm']:,.0f}")
```

### 2.3 Full CCR Metrics

```python
from qlrisk.engine import CCREngine

with CCREngine() as engine:
    trade_data = {
        'trade_id': 'IRS-001',
        'notional': 10_000_000,
        'mtm': 250_000,
        'maturity': 5.0,
        'volatility': 0.20,
        'counterparty_pd': 0.02,
        'counterparty_lgd': 0.45,
        'discount_rate': 0.03,
        'spread': 0.015,
        'recovery_rate': 0.40,
        'confidence_level': 0.99
    }
    
    results = engine.calculate_ccr_metrics(trade_data)
    
    print("CCR Metrics Summary:")
    print(f"  PD:               {results['pd']:.4%}")
    print(f"  LGD:              {results['lgd']:.2%}")
    print(f"  EAD:              ${results['ead']:,.2f}")
    print(f"  Expected Loss:    ${results['el']:,.2f}")
    print(f"  Current Exposure: ${results['current_exposure']:,.2f}")
    print(f"  Expected Exposure:${results['expected_exposure']:,.2f}")
    print(f"  PFE:              ${results.get('pfe', 0):,.2f}")
    print(f"  CVA:              ${results.get('cva', 0):,.2f}")
    print(f"  Economic Capital: ${results.get('economic_capital', 0):,.2f}")
```

---

## 3. Basic Usage

### 3.1 Using the Calculator Factory

```python
from qlrisk.calculator import CalculatorFactory, CalculatorType

# Get factory instance (singleton)
factory = CalculatorFactory.get_instance()

# Get a Python calculator
pd_calc = factory.get_calculator(CalculatorType.PD, implementation='python')

# Calculate PD using rating-based method
result = pd_calc.calculate({
    'rating': 'A',
    'method': 'rating_based'
})
print(f"Rating A -> PD: {result.value:.4%}")

# Calculator details
print(f"Calculator: {result.calculator_name}")
print(f"Type: {result.calculator_type.value}")
```

### 3.2 Available Calculator Types

```python
from qlrisk.calculator import CalculatorType

# List all calculator types
for calc_type in CalculatorType:
    print(f"  {calc_type.name}: {calc_type.value}")
```

Output:
```
  PD: probability_of_default
  LGD: loss_given_default
  EAD: exposure_at_default
  EL: expected_loss
  CE: current_exposure
  PFE: potential_future_exposure
  EE: expected_exposure
  EEE: effective_expected_exposure
  PEAK_EXPOSURE: peak_exposure
  STRESSED_EXPOSURE: stressed_exposure
  CVA: credit_valuation_adjustment
  EC: economic_capital
  RAROC: risk_adjusted_return_on_capital
  IM: initial_margin
  MTM: mark_to_market
  NPV: net_present_value
```

### 3.3 Direct Calculator Usage

```python
from qlrisk.calculator import CalculatorFactory, CalculatorType

factory = CalculatorFactory.get_instance()

# PD Calculator
pd_calc = factory.get_calculator(CalculatorType.PD)
pd_result = pd_calc.calculate({'rating': 'BBB', 'method': 'rating_based'})

# LGD Calculator  
lgd_calc = factory.get_calculator(CalculatorType.LGD)
lgd_result = lgd_calc.calculate({
    'seniority': 'senior_secured',
    'collateral_value': 5_000_000,
    'exposure': 10_000_000
})

# EAD Calculator
ead_calc = factory.get_calculator(CalculatorType.EAD)
ead_result = ead_calc.calculate({
    'current_exposure': 250_000,
    'undrawn_commitment': 750_000,
    'ccf': 0.5
})

# Expected Loss
el_calc = factory.get_calculator(CalculatorType.EL)
el_result = el_calc.calculate({
    'pd': pd_result.value,
    'lgd': lgd_result.value,
    'ead': ead_result.value
})

print(f"PD:  {pd_result.value:.4%}")
print(f"LGD: {lgd_result.value:.2%}")
print(f"EAD: ${ead_result.value:,.2f}")
print(f"EL:  ${el_result.value:,.2f}")
```

---

## 4. Calculator Examples

### 4.1 Probability of Default (PD)

```python
from qlrisk.calculator import CalculatorFactory, CalculatorType

factory = CalculatorFactory.get_instance()
pd_calc = factory.get_calculator(CalculatorType.PD)

# Method 1: Rating-based PD
result = pd_calc.calculate({
    'method': 'rating_based',
    'rating': 'BBB'
})
print(f"Rating-based PD (BBB): {result.value:.4%}")

# Method 2: Merton model
result = pd_calc.calculate({
    'method': 'merton',
    'asset_value': 100_000_000,
    'debt': 60_000_000,
    'asset_volatility': 0.25,
    'time_horizon': 1.0,
    'risk_free_rate': 0.03
})
print(f"Merton PD: {result.value:.4%}")
```

### 4.2 Credit Valuation Adjustment (CVA)

```python
from qlrisk.calculator import CalculatorFactory, CalculatorType

factory = CalculatorFactory.get_instance()
cva_calc = factory.get_calculator(CalculatorType.CVA)

result = cva_calc.calculate({
    'ee_profile': [100000, 150000, 200000, 180000, 150000, 100000],
    'time_grid': [0.5, 1.0, 2.0, 3.0, 4.0, 5.0],
    'credit_spread': 0.015,  # 150 bps
    'recovery_rate': 0.40,
    'risk_free_rate': 0.03
})

print(f"CVA: ${result.value:,.2f}")
```

### 4.3 Potential Future Exposure (PFE)

```python
from qlrisk.calculator import CalculatorFactory, CalculatorType

factory = CalculatorFactory.get_instance()
pfe_calc = factory.get_calculator(CalculatorType.PFE)

result = pfe_calc.calculate({
    'current_mtm': 500_000,
    'notional': 10_000_000,
    'remaining_maturity': 5.0,
    'volatility': 0.20,
    'confidence_level': 0.95,
    'product_type': 'irs'
})

print(f"PFE (95%): ${result.value:,.2f}")
```

### 4.4 Economic Capital

```python
from qlrisk.calculator import CalculatorFactory, CalculatorType

factory = CalculatorFactory.get_instance()
ec_calc = factory.get_calculator(CalculatorType.EC)

result = ec_calc.calculate({
    'exposures': [1_000_000, 2_000_000, 500_000],
    'pds': [0.02, 0.01, 0.05],
    'lgds': [0.45, 0.40, 0.50],
    'asset_correlation': 0.20,
    'confidence_level': 0.999
})

print(f"Economic Capital: ${result.value:,.2f}")
```

### 4.5 Stress Testing

```python
from qlrisk.calculator import CalculatorFactory, CalculatorType

factory = CalculatorFactory.get_instance()
stress_calc = factory.get_calculator(CalculatorType.STRESSED_EXPOSURE)

# Historical stress scenario
result = stress_calc.calculate({
    'base_exposure': 10_000_000,
    'stress_type': 'historical',
    'stress_scenario': '2008_crisis',
    'product_type': 'irs',
    'sensitivities': {
        'dv01': 50_000,
        'duration': 4.5,
        'fx_delta': 0,
        'vega': 25_000
    }
})

print(f"Base Exposure: $10,000,000")
print(f"Stressed Exposure: ${result.value:,.2f}")
```

---

## 5. Data Generation

### 5.1 Quick Dataset

```python
from qlrisk.data import create_test_dataset

# Create dataset with specific number of trades
dataset = create_test_dataset(
    num_trades=1000,      # Approximate number of trades
    seed=42               # For reproducibility
)

print(f"Generated:")
print(f"  Counterparties: {dataset['summary']['num_counterparties']}")
print(f"  Trades: {dataset['summary']['num_trades']}")
print(f"  Total Notional: ${dataset['summary']['total_notional']:,.0f}")
```

### 5.2 Detailed Data Generation

```python
from qlrisk.data import DataGenerator, ProductType

# Create generator with seed for reproducibility
generator = DataGenerator(seed=42)

# Generate counterparties
counterparties = []
for _ in range(10):
    cp = generator.generate_counterparty()
    counterparties.append(cp)
    print(f"  {cp.counterparty_id}: {cp.name} ({cp.rating.name}, PD={cp.pd:.4%})")

# Generate trades for each counterparty
trades = []
for cp in counterparties:
    # Generate 5 trades per counterparty
    for product_type in [ProductType.IRS, ProductType.FX_FORWARD, ProductType.CDS]:
        trade = generator.generate_trade(cp.counterparty_id, product_type)
        trades.append(trade)

print(f"\nGenerated {len(trades)} trades")
```

### 5.3 Generate Market Data

```python
from qlrisk.data import DataGenerator

generator = DataGenerator(seed=42)
market_data = generator.generate_market_data()

print("Market Data:")
print(f"  Valuation Date: {market_data.valuation_date}")
print(f"  Base Currency: {market_data.base_currency}")
print(f"  Discount Rate: {market_data.discount_rate:.2%}")
print(f"  FX Rates: {list(market_data.fx_rates.keys())}")
print(f"  Yield Curves: {list(market_data.yield_curves.keys())}")
```

### 5.4 Generate Stress Scenarios

```python
from qlrisk.data import DataGenerator

generator = DataGenerator(seed=42)
base_market = generator.generate_market_data()
scenarios = generator.generate_stress_scenarios(base_market, num_scenarios=5)

print(f"Generated {len(scenarios)} stress scenarios:")
for scenario in scenarios:
    print(f"  - {scenario.metadata.get('scenario_name', 'unnamed')}")
```

---

## 6. Path Generation

### 6.1 Geometric Brownian Motion (GBM)

```python
from qlrisk.mathlib import MathFactory, PathGenerationParams, ProcessType

# Get factory and create path generator
factory = MathFactory.get_instance()
path_gen = factory.create_path_generator(implementation='python')

# Configure simulation parameters
params = PathGenerationParams(
    initial_value=100.0,
    drift=0.05,           # 5% annual drift
    volatility=0.20,      # 20% annual volatility
    maturity=1.0,         # 1 year
    num_steps=252,        # Daily steps
    num_paths=10000       # 10,000 paths
)

# Generate paths
result = path_gen.generate_paths(params, ProcessType.GBM)

print(f"Path shape: {result.paths.shape}")
print(f"Initial value: {params.initial_value}")
print(f"Final mean: {result.paths[:, -1].mean():.2f}")
print(f"Final std: {result.paths[:, -1].std():.2f}")
print(f"95th percentile: {sorted(result.paths[:, -1])[int(0.95 * len(result.paths))]:.2f}")
```

### 6.2 Mean-Reverting Process (Ornstein-Uhlenbeck)

```python
from qlrisk.mathlib import MathFactory, PathGenerationParams, ProcessType

factory = MathFactory.get_instance()
path_gen = factory.create_path_generator()

params = PathGenerationParams(
    initial_value=0.05,   # Starting rate
    drift=0.04,           # Long-term mean (theta)
    volatility=0.01,      # Volatility (sigma)
    maturity=5.0,         # 5 years
    num_steps=60,         # Monthly
    num_paths=5000,
    mean_reversion=0.5    # Mean reversion speed (kappa)
)

result = path_gen.generate_paths(params, ProcessType.ORNSTEIN_UHLENBECK)
print(f"OU Process - Final mean: {result.paths[:, -1].mean():.4f}")
```

### 6.3 CIR Process (Interest Rates)

```python
from qlrisk.mathlib import MathFactory, PathGenerationParams, ProcessType

factory = MathFactory.get_instance()
path_gen = factory.create_path_generator()

params = PathGenerationParams(
    initial_value=0.03,   # Starting rate
    drift=0.04,           # Long-term mean
    volatility=0.02,      # Volatility
    maturity=10.0,        # 10 years
    num_steps=120,        # Monthly
    num_paths=5000,
    mean_reversion=0.3
)

result = path_gen.generate_paths(params, ProcessType.CIR)
print(f"CIR Process - Final mean: {result.paths[:, -1].mean():.4f}")
```

---

## 7. Configuration

### 7.1 Loading Configuration

```python
from qlrisk.core import PropertiesConfigurator

# Load configuration file
config = PropertiesConfigurator('config/application.properties')

# Get values with type conversion
max_workers = config.get_int('engine.max_workers', default=8)
confidence = config.get_float('calculator.confidence_level', default=0.99)
implementation = config.get('engine.default_implementation', default='python')

print(f"Max Workers: {max_workers}")
print(f"Confidence Level: {confidence}")
print(f"Implementation: {implementation}")
```

### 7.2 Configuration File Format

```properties
# config/application.properties

# Engine Configuration
engine.max_workers=8
engine.default_implementation=python
engine.timeout=300

# Monte Carlo Settings
montecarlo.num_paths=10000
montecarlo.num_steps=252
montecarlo.seed=42

# Calculator Defaults
calculator.confidence_level=0.99
calculator.time_horizon=1.0

# PFE Settings
calculator.pfe.confidence_level=0.95

# CVA Settings
calculator.cva.integration_points=100

# Logging
logging.level=INFO
logging.file=ccr_analytics.log
```

### 7.3 Runtime Configuration

```python
from qlrisk.core import PropertiesConfigurator

config = PropertiesConfigurator()

# Set values at runtime
config.set('engine.max_workers', 16)
config.set('montecarlo.num_paths', 50000)

# Runtime values take precedence over file values
print(f"Workers: {config.get_int('engine.max_workers')}")
```

---

## 8. Troubleshooting

### 8.1 Common Issues

**Import Error: No module named 'qlrisk'**
```bash
# Ensure you're in the correct directory
cd /path/to/qlrisk/parent
python -c "import qlrisk"

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/qlrisk/parent"
```

**QuantLib Not Found**
```python
# Check if QuantLib is available
try:
    import QuantLib
    print(f"QuantLib version: {QuantLib.__version__}")
except ImportError:
    print("QuantLib not installed - using Python implementation")
    print("Install with: pip install QuantLib-Python")
```

**Configuration File Not Found**
```python
import os
config_path = 'config/application.properties'
if not os.path.exists(config_path):
    print(f"Config not found: {config_path}")
    print("Using default configuration")
```

### 8.2 Logging

```python
from qlrisk.core import get_logger
import logging

# Get logger
logger = get_logger(__name__)

# Set debug level
logger.setLevel(logging.DEBUG)

# Log messages
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### 8.3 Memory Issues with Large Simulations

```python
from qlrisk.mathlib import PathGenerationParams

# Reduce simulation size
params = PathGenerationParams(
    initial_value=100.0,
    drift=0.05,
    volatility=0.20,
    maturity=1.0,
    num_steps=50,      # Reduce from 252
    num_paths=1000     # Reduce from 10000
)

# Or process in batches
batch_size = 1000
total_paths = 10000
for i in range(0, total_paths, batch_size):
    params.num_paths = min(batch_size, total_paths - i)
    result = path_gen.generate_paths(params, ProcessType.GBM)
    # Process batch...
```

### 8.4 Performance Tips

1. **Use QuantLib** for production workloads (2-3x faster)
2. **Increase thread count** for I/O-bound operations
3. **Pre-generate paths** for portfolio calculations
4. **Cache discount factors** when reusing curves
5. **Use vectorized operations** via NumPy

### 8.5 Getting Help

- Review documentation in `docs/` directory
- Check `docs/mathematical_formulas.md` for formulas
- Check `docs/architecture.md` for system design
- Contact: ajsinha@gmail.com

---

*Document Version: 2.1.0*  
*Last Updated: December 2025*  
*Copyright © 2025-2030 Ashutosh Sinha. All Rights Reserved.*
