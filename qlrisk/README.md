# QLRisk v1.3.0

**Comprehensive Counterparty Credit Risk Analytics Platform**

---

## Copyright Notice

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This software and its associated documentation are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
```

---

## Overview

QLRisk is a professional-grade Python library for comprehensive counterparty credit risk (CCR) analytics. It provides complete implementations of exposure calculations, valuation adjustments, regulatory capital metrics, and a wide range of financial product models.

### Key Highlights

- **90+ Financial Products** across 13 asset classes with full pricing and CCR exposure calculation
- **16 Risk Calculators** with dual Python and QuantLib implementations
- **55+ Domain Models** for trades, portfolios, counterparties, curves, and scenarios
- **7 Stochastic Processes** for Monte Carlo simulation (GBM, OU, CIR, Vasicek, Hull-White, Heston, Merton Jump)
- **Multi-threaded Engine** for high-performance parallel computation
- **SA-CCR Implementation** fully compliant with Basel III/IV regulatory framework
- **XVA Suite** including CVA, DVA, FVA, KVA, MVA, and ColVA calculations
- **Comprehensive SFT Coverage** including Stock Loans, Securities Borrowing, Collateral Swaps, Prime Brokerage
- **Total Return Swaps** for Equity and Bond underlyings with full CCR analytics

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Project Structure](#project-structure)
5. [Module Reference](#module-reference)
6. [Usage Examples](#usage-examples)
7. [Configuration](#configuration)
8. [Performance](#performance)
9. [Documentation](#documentation)
10. [Version History](#version-history)
11. [License](#license)

---

## Features

### Financial Products (90+ Implementations)

| Category | Count | Products |
|----------|-------|----------|
| **Interest Rate** | 8 | IRS, OIS, FRA, Cap, Floor, Swaption, Basis Swap, IRSLeg |
| **FX** | 6 | Forward, Swap, Option, Barrier Option, NDF, Digital Option |
| **Credit** | 4 | CDS, CDS Index, Total Return Swap, Credit Linked Note |
| **Equity Derivatives** | 6 | Swap, Option, Forward, Variance Swap, Dividend Swap, **Equity TRS** |
| **Commodity** | 3 | Swap, Option, Forward |
| **Cross-Currency** | 3 | XCCY Swap, Basis Swap, MTM Swap |
| **Repo** | 4 | Repo, Reverse Repo, Securities Lending, Buy/Sell Back |
| **SFT** | 7 | Margin Loan, Margin Lending, Collateral Swap, Tri-Party Repo, Prime Brokerage, Securities Borrowing, **Stock Loan** |
| **Money Market** | 7 | CD, BA, Eurodollar, Fed Funds, MMF, Time Deposit, Discount Note |
| **Stocks & ETFs** | 8 | Common Stock, ADR, GDR, Preferred, Warrant, ETF, Mutual Fund, Index Position |
| **Alternatives** | 8 | Crypto (Spot/Future/Perpetual), REIT, Carbon Credit/Future, PE, Hedge Fund |
| **Futures** | 6 | Index, Interest Rate, Bond, VIX, Single Stock, **Commodity Future** |
| **Fixed Income** | 21 | Treasury (Bill/Note/Bond/TIPS), Gilts, Bunds, JGB, OAT, Muni, Agency, Corporate, FRN, Convertible, CP, MTN, MBS, ABS, CDO, CLO, Zero Coupon, **Bond TRS** |

### Risk Calculators (16 Types)

| Category | Calculator | Description |
|----------|------------|-------------|
| **Credit Risk** | `PD` | Probability of Default (Merton, Rating-based, Reduced-form) |
| | `LGD` | Loss Given Default (Workout, Market-implied) |
| | `EAD` | Exposure at Default (Current, Regulatory) |
| | `EL` | Expected Loss = PD × LGD × EAD |
| **Exposure** | `CE` | Current Exposure (MTM, Collateral-adjusted) |
| | `PFE` | Potential Future Exposure (Monte Carlo, Parametric) |
| | `EE` | Expected Exposure Profile |
| | `EEE` | Effective Expected Exposure (Non-decreasing EE) |
| | `PEAK_EXPOSURE` | Maximum Exposure over time horizon |
| | `STRESSED_EXPOSURE` | Stressed market scenarios |
| **Valuation Adjustments** | `CVA` | Credit Valuation Adjustment |
| **Capital & Margin** | `EC` | Economic Capital (Vasicek, Gordy, Basel IRB) |
| | `RAROC` | Risk-Adjusted Return on Capital |
| | `IM` | Initial Margin (ISDA SIMM) |

### Domain Models (55+ Types)

| Module | Models |
|--------|--------|
| **Trade** | Trade, TradeType, TradeStatus |
| **Portfolio** | Portfolio, PortfolioSnapshot, PortfolioSummary |
| **Counterparty** | Counterparty, NettingSet, CollateralAgreement |
| **Curve** | YieldCurve, CreditCurve, VolatilitySurface |
| **Market Data** | MarketData, MarketDataSnapshot, Quote |
| **Scenario** | Scenario, ScenarioSet, MonteCarloScenarioSet |
| **Exposure** | ExposureProfile, ExposureResult, SACCRResult |
| **Rating** | CreditRating, RatingHistory, TransitionMatrix |

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Install Dependencies

```bash
# Required
pip install numpy scipy

# Optional: QuantLib for high-performance calculations
pip install QuantLib-Python
```

### Running the Demo

```bash
# Quick demo
python main.py --quick

# Full demonstration
python main.py

# Performance benchmarks
python main.py --benchmark

# Stress testing
python main.py --stress

# Or run as module
python -m qlrisk --quick
```

---

## Quick Start

### Basic CCR Calculation

```python
from qlrisk.engine import CCREngine
from qlrisk.calculator import CalculatorType

with CCREngine() as engine:
    # Calculate probability of default
    pd_result = engine.calculate(CalculatorType.PD, {
        'rating': 'BBB',
        'method': 'rating_based'
    })
    print(f"PD: {pd_result.value:.4%}")
```

### Generate Test Data

```python
from qlrisk.data import DataGenerator, create_test_dataset

# Quick dataset
dataset = create_test_dataset(num_trades=1000)
print(f"Generated {dataset['summary']['num_trades']} trades")
```

### Path Generation

```python
from qlrisk.mathlib import MathFactory, PathGenerationParams, ProcessType

factory = MathFactory.get_instance()
path_gen = factory.create_path_generator(implementation='python')

params = PathGenerationParams(
    initial_value=100.0,
    drift=0.05,
    volatility=0.20,
    maturity=1.0,
    num_steps=252,
    num_paths=10000
)

result = path_gen.generate_paths(params, ProcessType.GBM)
print(f"Final mean: {result.paths[:, -1].mean():.2f}")
```

---

## Project Structure

```
qlrisk/
├── __init__.py              # Package initialization (v1.3.0)
├── __main__.py              # Entry point for python -m
├── main.py                  # Main demonstration script
├── core/                    # Core utilities (9 files)
├── calculator/              # Risk calculators (29 files)
│   ├── python/              # Python implementations
│   └── qlib/                # QuantLib implementations
├── products/                # Financial products (90+ files)
│   ├── python/              # 80 Python products
│   └── qlib/                # QuantLib products
├── models/                  # Domain models (14 files)
├── mathlib/                 # Mathematical library (6 files)
├── engine/                  # CCR Engine (2 files)
├── data/                    # Data generation (2 files)
├── config/                  # Configuration
└── docs/                    # Documentation (130+ files)
```

---

## Configuration

Configuration file: `config/application.properties`

```properties
engine.max_workers=8
engine.default_implementation=python
montecarlo.num_paths=10000
calculator.confidence_level=0.99
logging.level=INFO
```

---

## Performance

| Operation | Python | QuantLib | Speedup |
|-----------|--------|----------|---------|
| PD Calculation | 0.05ms | 0.02ms | 2.5x |
| CVA (100 points) | 2.5ms | 0.8ms | 3.1x |
| PFE Monte Carlo | 150ms | 45ms | 3.3x |

---

## Documentation

See the `docs/` directory for comprehensive documentation:

- `docs/architecture.md` - System architecture
- `docs/quickstart.md` - Getting started guide
- `docs/mathematical_formulas.md` - Mathematical reference
- `docs/calculators/` - Calculator documentation
- `docs/products/` - Product documentation (80+ files)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **v1.3.0** | Dec 2025 | Documentation overhaul, import fixes, version sync |
| v1.2.0 | Dec 2025 | XVA calculators, SA-CCR, 80 products |
| v1.1.0 | Dec 2025 | Expanded products, documentation |
| v1.0.0 | Dec 2025 | Initial release |

---

## License

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

PROPRIETARY AND CONFIDENTIAL
```

---

*QLRisk v1.3.0 | Copyright © 2025-2030 Ashutosh Sinha*
