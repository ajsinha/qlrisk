# QLRisk - Documentation v2.2.1

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the software it describes are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
```

---

## Documentation Index

Welcome to QLRisk documentation. QLRisk is a unified market risk and counterparty credit risk analytics platform — **Every risk. One engine.**
This guide covers pricing and sensitivities, counterparty credit risk and XVA, and the market-risk roadmap
(VaR, Expected Shortfall, stress testing, backtesting and FRTB).

### Quick Links

| Document | Description |
|----------|-------------|
| [guides/](guides/README.md) | **User guides with tested, working examples (start here)** |
| [README.md](../README.md) | Main project README with overview |
| [quickstart.md](quickstart.md) | Getting started guide with examples |
| [architecture.md](architecture.md) | System architecture and design |
| [mathematical_formulas.md](mathematical_formulas.md) | Mathematical foundations |
| [saccr.md](saccr.md) | SA-CCR methodology documentation |
| [market_risk/README.md](market_risk/README.md) | Market-risk roadmap: VaR, ES, sensitivities, stress, backtesting, FRTB |
| [market_risk/risk_factors.md](market_risk/risk_factors.md) | Risk-factor keys, shocks, dependency detection, factor histories |
| [market_risk/sensitivities.md](market_risk/sensitivities.md) | DV01, CS01, delta, gamma, vega, theta, cross-gamma, tenor ladders |
| [market_risk/pricers.md](market_risk/pricers.md) | Analytic pricers and product terms |
| [market_risk/var_es.md](market_risk/var_es.md) | VaR / ES / SVaR methodology, scenarios, decomposition |
| [market_risk/validation.md](market_risk/validation.md) | Backtesting, P&L explain, PLA, stress library, reverse stress, LVaR |
| [market_risk/frtb.md](market_risk/frtb.md) | FRTB SA / IMA, Basel 2.5, BA-CVA: methodology, parameters, simplifications |
| [Brand kit](../assets/branding/BRAND.md) | Logo, favicon, tagline and palette |

---

## Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
├── architecture.md              # System architecture (detailed)
├── quickstart.md                # Getting started guide
├── mathematical_formulas.md     # Mathematical reference
├── saccr.md                     # SA-CCR implementation details
│
├── guides/                      # User guides (examples run in the test suite)
│   ├── getting_started/        # installation, first portfolio
│   ├── market_data/            # building market data, shocks, histories
│   ├── pricing/                # pricing every product family
│   ├── market_risk/            # sensitivities, VaR/ES, backtesting and stress
│   ├── regulatory/             # FRTB SA / IMA, Basel 2.5, BA-CVA
│   ├── reporting/              # RiskEngine, hierarchies, limits, export
│   └── counterparty_risk/      # exposure, SA-CCR, CCR metrics
│
├── market_risk/                 # Market-risk roadmap and methodology
│   ├── README.md               # Module plan by phase
│   ├── risk_factors.md         # Risk-factor keys, shocks, histories
│   ├── sensitivities.md        # Bump-and-reprice sensitivities, ladders
│   ├── pricers.md              # Analytic pricers and product kwargs
│   ├── var_es.md               # VaR / ES / SVaR methodology
│   ├── validation.md           # Backtesting, PLA, stress, reverse stress
│   └── frtb.md                 # Regulatory capital methodology
│
├── calculators/                 # Calculator documentation (18 files)
│   ├── README.md               # Calculator overview
│   ├── pd_calculator.md        # Probability of Default
│   ├── lgd_calculator.md       # Loss Given Default
│   ├── ead_calculator.md       # Exposure at Default
│   ├── el_calculator.md        # Expected Loss
│   ├── ce_calculator.md        # Current Exposure
│   ├── pfe_calculator.md       # Potential Future Exposure
│   ├── ee_calculator.md        # Expected Exposure
│   ├── cva_calculator.md       # Credit Valuation Adjustment
│   ├── dva_calculator.md       # Debit Valuation Adjustment
│   ├── fva_calculator.md       # Funding Valuation Adjustment
│   ├── kva_calculator.md       # Capital Valuation Adjustment
│   ├── mva_calculator.md       # Margin Valuation Adjustment
│   ├── ec_calculator.md        # Economic Capital
│   ├── raroc_calculator.md     # Risk-Adjusted Return on Capital
│   ├── im_calculator.md        # Initial Margin
│   ├── saccr_calculator.md     # SA-CCR EAD Calculator
│   └── stress_calculators.md   # Stress Testing
│
├── models/                      # Model documentation (10 files)
│   ├── README.md               # Models overview
│   ├── trade.md                # Trade model
│   ├── portfolio.md            # Portfolio model
│   ├── counterparty.md         # Counterparty model
│   ├── curve.md                # Curve models
│   ├── market_data.md          # Market data model
│   ├── products.md             # Product definitions
│   ├── scenario.md             # Scenario model
│   ├── exposure.md             # Exposure model
│   └── rating.md               # Rating model
│
├── metrics/                     # Metrics documentation (5 files)
│   ├── cva.md                  # CVA methodology
│   ├── pfe.md                  # PFE methodology
│   ├── epe.md                  # EPE methodology
│   ├── expected_loss.md        # EL methodology
│   └── economic_capital.md     # EC methodology
│
└── products/                    # Product documentation (80+ files)
    ├── README.md               # Products overview
    ├── interest_rate/          # Interest rate products (7 files)
    ├── fx/                     # FX products (6 files)
    ├── credit/                 # Credit products (4 files)
    ├── equity/                 # Equity products (5 files)
    ├── commodity/              # Commodity products (3 files)
    ├── cross_currency/         # Cross-currency products (3 files)
    ├── repo/                   # Repo products (4 files)
    ├── money_market/           # Money market products (7 files)
    ├── stocks/                 # Stock products (8 files)
    ├── alternatives/           # Alternative products (8 files)
    ├── futures/                # Futures products (5 files)
    └── fixed_income/           # Fixed income products (20 files)
```

---

## System Overview

### Component Summary

| Component | Files | Description |
|-----------|-------|-------------|
| **Products** | 81 | Financial products across 12 asset classes |
| **Calculators** | 16 | Risk calculators (Python + QuantLib) |
| **Models** | 55+ | Domain model classes |
| **Stochastic Processes** | 8 | Path generation algorithms |
| **Core Utilities** | 8 | Logging, config, timing, validation |

### Product Categories

| Category | Count | Examples |
|----------|-------|----------|
| Interest Rate | 8 | IRS, OIS, FRA, Cap, Floor, Swaption |
| FX | 6 | Forward, Swap, Option, Barrier, NDF |
| Credit | 4 | CDS, CDS Index, TRS, CLN |
| Equity | 5 | Swap, Option, Forward, Variance Swap |
| Commodity | 3 | Swap, Option, Forward |
| Cross-Currency | 3 | XCCY Swap, Basis Swap, MTM Swap |
| Repo | 4 | Repo, Reverse Repo, Securities Lending |
| Money Market | 7 | CD, BA, Eurodollar, Fed Funds |
| Stocks | 8 | Common, ADR, GDR, ETF, Warrant |
| Alternatives | 8 | Crypto, REIT, Carbon, PE, Hedge Fund |
| Futures | 5 | Index, IR, Bond, VIX, Single Stock |
| Fixed Income | 20 | Treasuries, Gilts, MBS, CDO, CLO |

### Calculator Types

| Category | Calculators |
|----------|-------------|
| Credit Risk | PD, LGD, EAD, EL |
| Exposure | CE, PFE, EE, EEE, Peak, Stressed |
| Valuation | CVA, DVA, FVA, KVA, MVA |
| Capital | EC, RAROC, IM |
| Regulatory | SA-CCR |
| Market Risk | Sensitivities ✅, VaR (HS/filtered/MC/parametric) ✅, ES ✅, SVaR ✅, decomposition ✅, backtesting ✅, PLA ✅, stress library ✅, reverse stress ✅, FRTB SA/IMA ✅, Basel 2.5 ✅, BA-CVA ✅; planned: SA-CVA |

---

## Getting Started

1. **Installation**: See [quickstart.md](quickstart.md#1-installation)
2. **Basic Usage**: See [quickstart.md](quickstart.md#2-quick-start)
3. **Architecture**: See [architecture.md](architecture.md)
4. **Formulas**: See [mathematical_formulas.md](mathematical_formulas.md)

---

## API Reference

### Core Module

```python
from qlrisk.core import (
    PropertiesConfigurator,  # Configuration management
    get_logger,              # Logging utilities
    Timer,                   # Performance timing
    ThreadPoolManager,       # Thread pool management
    Validators,              # Input validation
    DateUtils,               # Date calculations
    NumericUtils,            # Numerical utilities
)
```

### Calculator Module

```python
from qlrisk.calculator import (
    CalculatorFactory,       # Factory for calculators
    CalculatorType,          # Calculator type enum
    CalculationResult,       # Result container
    ImplementationType,      # Python or QuantLib
)
```

### Engine Module

```python
from qlrisk.engine import (
    CCREngine,               # Main calculation engine
    EngineStatus,            # Engine status enum
    CalculationTask,         # Single task
    CalculationJob,          # Batch job
)
```

### Models Module

```python
from qlrisk.models import (
    Trade, TradeType,        # Trade models
    Portfolio,               # Portfolio aggregation
    Counterparty, NettingSet,# Counterparty models
    YieldCurve, CreditCurve, # Curve models
    Scenario, ScenarioSet,   # Stress scenarios
    ExposureProfile,         # Exposure results
    CreditRating,            # Rating models
)
```

### MathLib Module

```python
from qlrisk.mathlib import (
    MathFactory,             # Factory for math components
    ProcessType,             # Stochastic process types
    PathGenerationParams,    # Simulation parameters
    PathResult,              # Simulation results
)
```

### Data Module

```python
from qlrisk.data import (
    DataGenerator,           # Test data generator
    create_test_dataset,     # Quick dataset creation
    GeneratedTrade,          # Trade data class
    GeneratedCounterparty,   # Counterparty data class
)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **2.2.1** | Dec 2025 | Documentation overhaul, import fixes, version sync |
| 1.2.0 | Dec 2025 | XVA calculators, SA-CCR, 81 products |
| 1.1.0 | Dec 2025 | Expanded products, documentation |
| 1.0.0 | Dec 2025 | Initial release |

---

## Support

For questions or issues:
- Email: ajsinha@gmail.com
- Review specific documentation in this directory

---

*Document Version: 2.2.1*  
*Last Updated: December 2025*  
*Copyright © 2025-2030 Ashutosh Sinha. All Rights Reserved.*
