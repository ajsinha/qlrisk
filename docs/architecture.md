# QLRisk - Architecture Documentation v2.4.0

<!-- legacy-examples -->
> ⚠️ **Some code samples on this page predate v2.0 and no longer match the API** (6 of 7 fail). Use the [user guides](guides/README.md), whose examples are executed by the test suite, until this page is revised.
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

1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [Module Structure](#3-module-structure)
4. [Design Patterns](#4-design-patterns)
5. [Data Flow](#5-data-flow)
6. [Threading Model](#6-threading-model)
7. [Extension Points](#7-extension-points)
8. [Deployment Considerations](#8-deployment-considerations)

---

## 1. Overview

QLRisk is a high-performance, multi-threaded system for unified trading-book risk analytics — market risk and counterparty credit risk on one shared product, market-data and engine core ("Every risk. One engine."). Counterparty credit risk and XVA are implemented today; the market-risk layer (risk factors, sensitivities, VaR/ES, stress, backtesting, FRTB) is planned and specified in [market_risk/README.md](market_risk/README.md). It provides dual implementations (pure Python and QuantLib) for all calculations, enabling performance comparison and production flexibility.

### 1.1 Key Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Dual Implementation** | Every calculator has Python and QuantLib versions |
| **Multi-threaded** | Concurrent execution via ThreadPoolExecutor |
| **Modular Design** | Clean separation across 10 modules |
| **Factory Pattern** | Centralized object creation and caching |
| **Protocol-Based** | Type-safe interfaces using Python protocols |
| **Extensible** | Easy addition of new calculators, products, models |

### 1.2 Technology Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.9+ |
| **Numerical** | NumPy, SciPy |
| **Financial** | QuantLib-Python (optional) |
| **Concurrency** | concurrent.futures, threading |
| **Configuration** | Custom properties parser |
| **Logging** | Python logging with formatters |
| **Type Hints** | Full typing support |

### 1.3 System Statistics

| Metric | Count |
|--------|-------|
| Python Source Files | 172 |
| Documentation Files | 132 |
| Financial Products | 81 |
| Risk Calculators | 16 |
| Domain Models | 55+ |
| Stochastic Processes | 7 |
| Total Lines of Code | ~50,000 |

---

## 2. System Architecture

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           QLRisk v2.4.0                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                              ENGINE LAYER                                   │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │ │
│  │  │    CCREngine     │  │   TaskQueue      │  │  ThreadPool      │         │ │
│  │  │  - start/stop    │  │  - priority      │  │  - 8 workers     │         │ │
│  │  │  - calculate     │  │  - batching      │  │  - concurrent    │         │ │
│  │  │  - batch jobs    │  │  - callbacks     │  │  - futures       │         │ │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘         │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                          │
│                                       ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                           CALCULATOR LAYER                                  │ │
│  │  ┌─────────────────────────────┐    ┌─────────────────────────────┐       │ │
│  │  │    Python Calculators       │    │   QuantLib Calculators      │       │ │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐   │    │  ┌─────┐ ┌─────┐ ┌─────┐   │       │ │
│  │  │  │ PD  │ │ LGD │ │ EAD │   │    │  │ PD  │ │ LGD │ │ EAD │   │       │ │
│  │  │  └─────┘ └─────┘ └─────┘   │    │  └─────┘ └─────┘ └─────┘   │       │ │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐   │    │  ┌─────┐ ┌─────┐ ┌─────┐   │       │ │
│  │  │  │ CVA │ │ PFE │ │ EE  │   │    │  │ CVA │ │ PFE │ │ EE  │   │       │ │
│  │  │  └─────┘ └─────┘ └─────┘   │    │  └─────┘ └─────┘ └─────┘   │       │ │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐   │    │  ┌─────┐ ┌─────┐ ┌─────┐   │       │ │
│  │  │  │ EC  │ │ IM  │ │SACCR│   │    │  │ EC  │ │ IM  │ │SACCR│   │       │ │
│  │  │  └─────┘ └─────┘ └─────┘   │    │  └─────┘ └─────┘ └─────┘   │       │ │
│  │  └─────────────────────────────┘    └─────────────────────────────┘       │ │
│  │                        CalculatorFactory                                   │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                          │
│          ┌────────────────────────────┼────────────────────────────┐            │
│          ▼                            ▼                            ▼            │
│  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐      │
│  │   MODELS LAYER   │      │   PRODUCTS LAYER │      │   MATHLIB LAYER  │      │
│  │                  │      │                  │      │                  │      │
│  │  Trade           │      │  Interest Rate   │      │  PathGenerator   │      │
│  │  Portfolio       │      │  FX              │      │  - GBM           │      │
│  │  Counterparty    │      │  Credit          │      │  - OU            │      │
│  │  NettingSet      │      │  Equity          │      │  - CIR           │      │
│  │  YieldCurve      │      │  Commodity       │      │  - Vasicek       │      │
│  │  CreditCurve     │      │  CrossCurrency   │      │  - Hull-White    │      │
│  │  Scenario        │      │  Repo            │      │  - Heston        │      │
│  │  ExposureProfile │      │  MoneyMarket     │      │  - Merton Jump   │      │
│  │  CreditRating    │      │  Stocks          │      │                  │      │
│  │                  │      │  Alternatives    │      │  MonteCarloEngine│      │
│  │  ModelFactory    │      │  Futures         │      │  StatisticalUtils│      │
│  │                  │      │  FixedIncome     │      │                  │      │
│  └──────────────────┘      └──────────────────┘      └──────────────────┘      │
│          │                            │                            │            │
│          └────────────────────────────┼────────────────────────────┘            │
│                                       ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                              CORE LAYER                                     │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │ │
│  │  │ Properties │ │   Logger   │ │   Timer    │ │ ThreadPool │              │ │
│  │  │Configurator│ │            │ │            │ │  Manager   │              │ │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘              │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │ │
│  │  │ Validators │ │ DateUtils  │ │NumericUtils│ │ Exceptions │              │ │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                          │
│  ┌────────────────┐  ┌────────────────┴───────────────┐  ┌────────────────┐    │
│  │   DATA LAYER   │  │        CONFIG LAYER            │  │   DOCS LAYER   │    │
│  │  DataGenerator │  │  application.properties        │  │  130+ markdown │    │
│  │  TestDataset   │  │  Environment Variables         │  │  files         │    │
│  └────────────────┘  └────────────────────────────────┘  └────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Module Dependencies

```
                    ┌─────────────┐
                    │   engine    │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ calculator │  │   models   │  │  mathlib   │
    └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                    ┌────────────┐
                    │  products  │
                    └──────┬─────┘
                           │
                           ▼
                    ┌────────────┐
                    │    core    │
                    └────────────┘
```

---

## 3. Module Structure

### 3.1 Core Module (`qlrisk/core/`)

Foundational utilities used across all modules.

| File | Class/Function | Description |
|------|----------------|-------------|
| `properties_configurator.py` | `PropertiesConfigurator` | Configuration with auto-reload, precedence chain |
| `logger.py` | `Logger`, `get_logger` | Thread-safe logging with formatting |
| `timer.py` | `Timer`, `timed` | Performance timing, context manager, decorator |
| `thread_pool.py` | `ThreadPoolManager` | Managed ThreadPoolExecutor wrapper |
| `exceptions.py` | `CCRException` hierarchy | ConfigurationError, CalculationError, ModelError, DataError, ValidationError, CurveError |
| `validators.py` | `Validators` | Input validation: not_none, positive, probability, in_range |
| `date_utils.py` | `DateUtils` | Business days, year fractions, schedule generation |
| `numeric_utils.py` | `NumericUtils` | Interpolation, norm_cdf/pdf/inv, statistics |

### 3.2 Calculator Module (`qlrisk/calculator/`)

All CCR metric calculators with dual implementations.

#### Base Components

| File | Class | Description |
|------|-------|-------------|
| `base.py` | `BaseCalculator` | Abstract base with calculate(), details() |
| `base.py` | `CalculatorType` | Enum: PD, LGD, EAD, EL, CE, PFE, EE, CVA, EC, RAROC, IM, etc. |
| `base.py` | `CalculationResult` | Result container with value, metadata, warnings |
| `base.py` | `ImplementationType` | PYTHON or QUANTLIB |
| `factory.py` | `CalculatorFactory` | Singleton factory with caching |

#### Python Implementations (`calculator/python/`)

| Calculator | Metrics | Methods |
|------------|---------|---------|
| `pd_calculator.py` | Probability of Default | Merton, Rating-based, Reduced-form |
| `lgd_calculator.py` | Loss Given Default | Workout, Market-implied, Regulatory |
| `ead_calculator.py` | Exposure at Default | Current, CCF-based, SA-CCR |
| `el_calculator.py` | Expected Loss | EL = PD × LGD × EAD |
| `ce_calculator.py` | Current Exposure | MTM-based, Collateral-adjusted |
| `pfe_calculator.py` | Potential Future Exposure | Monte Carlo, Parametric |
| `ee_calculator.py` | Expected Exposure | Profile generation, EPE, EEE |
| `cva_calculator.py` | Credit Valuation Adjustment | Unilateral, Bilateral |
| `ec_calculator.py` | Economic Capital | Vasicek, Gordy, Basel IRB |
| `raroc_calculator.py` | Risk-Adjusted Return | RAROC = (Revenue - EL) / EC |
| `im_calculator.py` | Initial Margin | ISDA SIMM methodology |
| `stress_calculators.py` | Stress Testing | Historical, Hypothetical, Reverse |
| `xva_calculators.py` | XVA Suite | DVA, FVA, KVA, MVA, ColVA |
| `saccr_calculator.py` | SA-CCR | Basel III/IV compliant |

#### QuantLib Implementations (`calculator/qlib/`)

Mirror implementations using QuantLib for enhanced performance.

### 3.3 Products Module (`qlrisk/products/`)

81 financial products across 12 asset classes.

| Category | Count | Products |
|----------|-------|----------|
| Interest Rate | 8 | InterestRateSwap, OvernightIndexSwap, ForwardRateAgreement, InterestRateCap, InterestRateFloor, Swaption, BasisSwap, IRSLeg |
| FX | 6 | FXForward, FXSwap, FXOption, FXBarrierOption, NonDeliverableForward, FXDigitalOption |
| Credit | 4 | CreditDefaultSwap, CDSIndex, TotalReturnSwap, CreditLinkedNote |
| Equity | 5 | EquitySwap, EquityOption, EquityForward, VarianceSwap, DividendSwap |
| Commodity | 3 | CommoditySwap, CommodityOption, CommodityForward |
| Cross-Currency | 3 | CrossCurrencySwap, CrossCurrencyBasisSwap, MTMCrossCurrencySwap |
| Repo | 4 | Repo, ReverseRepo, SecuritiesLending, BuySellBack |
| Money Market | 7 | CertificateOfDeposit, BankersAcceptance, EurodollarDeposit, FederalFunds, MoneyMarketFund, TimeDeposit, DiscountNote |
| Stocks | 8 | CommonStock, ADR, GDR, PreferredStock, Warrant, ETF, MutualFund, IndexPosition |
| Alternatives | 8 | CryptoSpot, CryptoFuture, CryptoPerpetual, REIT, CarbonCredit, CarbonFuture, PrivateEquityInterest, HedgeFundInterest |
| Futures | 5 | IndexFuture, InterestRateFuture, BondFuture, VIXFuture, SingleStockFuture |
| Fixed Income | 20 | TreasuryBill, TreasuryNote, TreasuryBond, TIPS, UKGilt, GermanBund, JGB, FrenchOAT, MunicipalBond, AgencyBond, CorporateBond, FloatingRateNote, ConvertibleBond, CommercialPaper, MediumTermNote, MBS, ABS, CDO, CLO, ZeroCouponBond |

### 3.4 Models Module (`qlrisk/models/`)

55+ domain models for market risk and CCR analytics.

| File | Models | Description |
|------|--------|-------------|
| `trade.py` | Trade, TradeType, TradeStatus | Trade representation |
| `portfolio.py` | Portfolio, PortfolioSnapshot, PortfolioSummary | Portfolio aggregation |
| `counterparty.py` | Counterparty, NettingSet, CollateralAgreement | Counterparty models |
| `curve.py` | Curve, YieldCurve, CreditCurve, VolatilitySurface | Market curves |
| `market_data.py` | MarketData, MarketDataSnapshot, Quote | Market data containers |
| `products.py` | 27 product model classes | Simplified product models |
| `scenario.py` | Scenario, ScenarioSet, MonteCarloScenarioSet | Stress testing |
| `exposure.py` | ExposureProfile, ExposureResult, SACCRResult | Exposure outputs |
| `rating.py` | CreditRating, RatingHistory, TransitionMatrix | Rating models |
| `collateral.py` | Collateral types and agreements | Collateral handling |
| `agreement.py` | Legal agreement models | ISDA, CSA |
| `limit.py` | Credit limit models | Limit monitoring |
| `factory.py` | ModelFactory | Model creation factory |

### 3.5 MathLib Module (`qlrisk/mathlib/`)

Mathematical utilities for simulation.

| Component | Description |
|-----------|-------------|
| `ProcessType` enum | GBM, ORNSTEIN_UHLENBECK, CIR, VASICEK, HULL_WHITE, HESTON, MERTON_JUMP |
| `PathGenerationParams` | initial_value, drift, volatility, maturity, num_paths, num_steps |
| `PathResult` | paths array, statistics, metadata |
| `BasePathGenerator` | Abstract path generator with Box-Muller |
| `MonteCarloConfig` | Simulation configuration |
| `MathFactory` | Factory for math components |

### 3.6 Engine Module (`qlrisk/engine/`)

Main execution engine.

| Component | Description |
|-----------|-------------|
| `CCREngine` | Main orchestrator: start(), stop(), calculate(), submit_job() |
| `EngineStatus` | IDLE, RUNNING, PAUSED, STOPPED, ERROR |
| `CalculationTask` | Single calculation with priority, callback |
| `CalculationJob` | Batch of tasks with parallel/sequential mode |
| `TaskResult` | Individual task result |
| `JobResult` | Batch job result with statistics |

### 3.7 Data Module (`qlrisk/data/`)

Test data generation.

| Component | Description |
|-----------|-------------|
| `DataGenerator` | Generates trades, counterparties, market data |
| `create_test_dataset()` | Quick dataset creation with num_trades parameter |
| `GeneratedTrade` | Trade data class |
| `GeneratedCounterparty` | Counterparty data class |
| `GeneratedMarketData` | Market data snapshot |
| `create_sample_market_data()` | Multi-asset `products.base.MarketData` for pricing demos and tests |
| `MarketHistoryGenerator` | Correlated, fat-tailed risk-factor histories with a stress regime |

### 3.8 Risk Factors Module (`qlrisk/riskfactors/`)

The layer shared by market risk and CCR. See [market_risk/risk_factors.md](market_risk/risk_factors.md).

| Component | Description |
|-----------|-------------|
| `taxonomy.py` | `RiskFactorKey` (`IR.FWD.SOFR.5Y`, `FX.EURUSD`, ...), `RiskClass`, `FactorKind` |
| `mapping.py` | Enumerate / read / write factors in `MarketData`; copy-on-write clone; dependency detection |
| `shocks.py` | Absolute / relative / log shocks; parallel, twist, butterfly curve shapes |
| `timeseries.py` | `RiskFactorTimeSeries`: histories, returns, gap filling, proxies, CSV |

### 3.9 Sensitivities Module (`qlrisk/sensitivities/`)

Bump-and-reprice risk for any product. See [market_risk/sensitivities.md](market_risk/sensitivities.md).

| Component | Description |
|-----------|-------------|
| `engine.py` | `SensitivityEngine`: central/forward differences, dependency-aware repricing, reporting currency, theta, cross-gamma |
| `measures.py` | DV01 / CS01 / DIV01 / DELTA / VEGA / THETA / CROSS_GAMMA and bump conventions |
| `results.py` | `SensitivityResult`: aggregation, ladders, export |
| `ladders.py` | Tenor ladders, re-bucketing onto standard and FRTB vertices |

```
products.price(MarketData) ◄── apply_shocks(base, factor ± bump) ◄── enumerate / detect factors
          │                                                     (riskfactors)
          └──► SensitivityResult (DV01, CS01, delta, vega, ...) ──► ladders / aggregation
```

### 3.10 Scenarios, P&L and Market Risk Engine

| Component | Description |
|-----------|-------------|
| `scenarios/` | `ScenarioSet` (returns matrix); historical, age-weighted, filtered, Monte Carlo, hypothetical; stress-window search |
| `pnl/` | `PnLMatrix` (trades x scenarios) with VaR / ES / Euler / incremental; full revaluation; Taylor P&L |
| `engine/market_risk_engine.py` | `MarketRiskEngine`: sensitivities, scenario P&L, VaR, ES, parametric VaR, stressed VaR, backtest, stress test, reverse stress, P&L explain, daily summary |
| `backtesting/` | VaR (Kupiec, Christoffersen, traffic light) and ES (Acerbi-Székely) backtests |
| `regulatory/` | FRTB SA (SBM, DRC, RRAO), FRTB IMA, Basel 2.5, BA-CVA, SA-CCR re-export ([frtb.md](market_risk/frtb.md)) |
| `engine/risk_engine.py` | `RiskEngine`: one call for PV, sensitivities, VaR/ES/SVaR, stress, backtest, FRTB SA, exposure; hierarchy + limits |
| `reporting/` | `Hierarchy` (additive sums, non-additive VaR/ES re-run per node), `RiskReport` (JSON/CSV), `RiskLimit` checks |

```
                     RiskEngine.run(trades, market_data, history, hierarchy, limits)
                                              │
        ┌──────────────┬───────────────┬──────┴────────┬────────────────┬──────────────┐
   Sensitivity    MarketRiskEngine   stress library   regulatory.frtb_sa   products: CCR
     Engine      (VaR/ES/SVaR/backtest)                                   exposure / SA-CCR
        └──────────────┴───────────────┴───────┬───────┴────────────────┴──────────────┘
                                         RiskReport ──► Hierarchy roll-up ──► limit checks ──► JSON / CSV
```

See [market_risk/var_es.md](market_risk/var_es.md).

---

## 4. Design Patterns

### 4.1 Factory Pattern

```py
class CalculatorFactory:
    """Singleton factory with calculator caching."""
    
    _instance = None
    _calculators: Dict[str, BaseCalculator] = {}
    
    @classmethod
    def get_instance(cls) -> 'CalculatorFactory':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_calculator(
        self,
        calc_type: CalculatorType,
        implementation: str = 'python'
    ) -> BaseCalculator:
        key = f"{calc_type.value}_{implementation}"
        if key not in self._calculators:
            self._calculators[key] = self._create(calc_type, implementation)
        return self._calculators[key]
```

### 4.2 Strategy Pattern

```text
class BaseCalculator(ABC):
    """Strategy interface for calculations."""
    
    @abstractmethod
    def _calculate_impl(self, data: Any) -> T:
        """Subclasses implement specific calculation logic."""
        pass
    
    def calculate(self, data: Any) -> CalculationResult:
        """Template method wrapping strategy."""
        result_value = self._calculate_impl(data)
        return CalculationResult(value=result_value, ...)
```

### 4.3 Protocol Pattern

```py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

class PathGeneratorLike(Protocol):
    """Protocol for path generators."""
    
    def generate_paths(
        self,
        params: PathGenerationParams,
        process_type: ProcessType = ProcessType.GBM
    ) -> PathResult:
        """Generate sample paths."""
        ...
    
    def generate_correlated_paths(
        self,
        params_list: List[PathGenerationParams],
        correlation_matrix: np.ndarray,
        process_type: ProcessType = ProcessType.GBM
    ) -> List[PathResult]:
        """Generate correlated paths for multiple assets."""
        ...
```

### 4.4 Context Manager Pattern

```py
class CCREngine:
    """Engine with context manager support."""
    
    def __enter__(self) -> 'CCREngine':
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()

# Usage
with CCREngine() as engine:
    result = engine.calculate(CalculatorType.PD, data)
```

### 4.5 Singleton Pattern

```py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

class PropertiesConfigurator:
    """
    Singleton thread-safe class for managing properties from configuration files.
    Supports property value resolution with ${...} patterns and auto-reload.

    Order of precedence (highest to lowest):
    1. Command line arguments (--key=value)
    2. Environment variables
    3. Property files (rightmost file has highest precedence)
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, properties_files: Union[str, List[str]] = None, reload_interval: int = 300):
        """
        Initialize the PropertiesConfigurator

        Args:
            properties_files: List of property file paths OR comma-delimited string of file paths
            reload_interval: Interval in seconds for auto-reload (default: 300 seconds = 5 minutes)
        """
        if hasattr(self, '_initialized'):
            return

        self._initialized = True

        # Parse properties_files - handle both string and list
        self._properties_files = self._parse_file_paths(properties_files)

        self._reload_interval = reload_interval
        self._properties: Dict[str, str] = {}
        self._properties_lock = threading.RLock()
        self._stop_reload = threading.Event()
        self._file_timestamps: Dict[str, float] = {}

        # Track source of each property: "commandline", "env", or "file"
        self._property_sources: Dict[str, str] = {}

        # Parse command line arguments (--key=value format)
        self._commandline_args: Dict[str, str] = {}
        self._parse_commandline_args()

        # Initial load
        self._load_properties()

        # Start auto-reload thread
        self._reload_thread = threading.Thread(target=self._auto_reload_worker, daemon=True)
        self._reload_thread.start()

    def _parse_file_paths(self, properties_files: Union[str, List[str], None]) -> List[str]:
        """
        Parse properties files input - handle both string and list formats

        Args:
            properties_files: String (comma-delimited) or list of file paths

        Returns:
            List of file paths
        """
        if properties_files is None:
            return []

        if isinstance(properties_files, str):
            # Split by comma and strip whitespace
            return [path.strip() for path in properties_files.split(',') if path.strip()]

        if isinstance(properties_files, list):
            return [str(path).strip() for path in properties_files if path]

        return []

    def _parse_commandline_args(self):
        """
        Parse command line arguments in --key=value format
        Stores them in _commandline_args dictionary
        """
        for arg in sys.argv[1:]:
            if arg.startswith('--') and '=' in arg:
                # Remove leading '--'
                arg = arg[2:]

                # Split by first '=' only
                key, value = arg.split('=', 1)
                key = key.strip()
                value = value.strip()

                if key:
                    self._commandline_args[key] = value

    def _load_properties(self):
        """
        Load properties from all configured files
        Files are processed in order, with rightmost file having highest precedence
        """
        with self._properties_lock:
            new_properties = {}
            new_sources = {}

            # Process files in order (left to right)
            # Later files will overwrite earlier ones, giving rightmost highest precedence
            for file_path in self._properties_files:
                if not os.path.exists(file_path):
                    continue

                # Track file modification time
                self._file_timestamps[file_path] = os.path.getmtime(file_path)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            line = line.strip()

                            # Skip empty lines and comments
                            if not line or line.startswith('#') or line.startswith('//'):
                                continue

                            # Split by first '=' only
                            if '=' not in line:
                                continue

                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()

                            if key:
                                # Rightmost file overwrites previous values
                                new_properties[key] = value
                                new_sources[key] = 'file'

                except Exception as e:
                    print(f"Error loading properties from {file_path}: {e}")

            # Resolve all property references (only for file-based properties)
            resolved_properties = self._resolve_all_properties(new_properties)

            # Now apply precedence: file < env < commandline
            final_properties = {}
            final_sources = {}

            for key in resolved_properties:
                # Start with file value (lowest precedence)
                value = resolved_properties[key]
                source = 'file'

                # Check environment variables (higher precedence)
                env_value = os.environ.get(key)
                if env_value is not None:
                    value = env_value
                    source = 'env'

                # Check command line arguments (highest precedence)
                if key in self._commandline_args:
                    value = self._commandline_args[key]
                    source = 'commandline'

                final_properties[key] = value
                final_sources[key] = source

            # Also add command-line only keys (not in files)
            for key, value in self._commandline_args.items():
                if key not in final_properties:
                    final_properties[key] = value
                    final_sources[key] = 'commandline'

            # Also add env-only keys (not in files or commandline)
            # Optional: You can enable this if you want ALL env vars accessible
            # for key, value in os.environ.items():
            #     if key not in final_properties:
            #         final_properties[key] = value
            #         final_sources[key] = 'env'

            self._properties = final_properties
            self._property_sources = final_sources

    def _resolve_all_properties(self, properties: Dict[str, str]) -> Dict[str, str]:
        """Resolve all ${...} references in properties"""
        resolved = {}

        for key, value in properties.items():
            resolved[key] = self._resolve_value(value, properties, set())

        return resolved

    def _resolve_value(self, value: str, properties: Dict[str, str], visited: set) -> str:
        """
        Recursively resolve ${...} references in a value, including nested references

        Args:
            value: The value to resolve
            properties: Dictionary of all properties
            visited: Set of keys already visited (to prevent circular references)

        Returns:
            Resolved value
        """
        if not value or '${' not in value:
            return value

        max_iterations = 100  # Prevent infinite loops
        iteration = 0

        while '${' in value and iteration < max_iterations:
            iteration += 1

            # Find innermost ${...} pattern
            pattern = r'\$\{([^{}]+)\}'
            matches = list(re.finditer(pattern, value))

            if not matches:
                # Handle nested patterns like ${x${y}}
                nested_pattern = r'\$\{([^}]*\$\{[^}]*\}[^}]*)\}'
                nested_matches = list(re.finditer(nested_pattern, value))

                if nested_matches:
                    # Process innermost references first
                    for match in reversed(nested_matches):
                        inner_ref = match.group(1)
                        resolved_inner = self._resolve_value(inner_ref, properties, visited)
                        value = value[:match.start()] + '${' + resolved_inner + '}' + value[match.end():]
                    continue
                else:
                    break

            # Replace all simple ${key} references
            for match in reversed(matches):
                ref_key = match.group(1)

                # Check for circular reference
                if ref_key in visited:
                    replacement = match.group(0)  # Keep original if circular
                else:
                    # Check command line args first (highest precedence)
                    replacement = self._commandline_args.get(ref_key)

                    # Then check environment variables
                    if replacement is None:
                        replacement = os.environ.get(ref_key)

                    # Finally check properties
                    if replacement is None:
                        replacement = properties.get(ref_key, match.group(0))

                        # Recursively resolve the replacement
                        if replacement != match.group(0):
                            new_visited = visited.copy()
                            new_visited.add(ref_key)
                            replacement = self._resolve_value(replacement, properties, new_visited)

                value = value[:match.start()] + replacement + value[match.end():]

        return value

    def _auto_reload_worker(self):
        """Worker thread for auto-reloading properties"""
        while not self._stop_reload.wait(self._reload_interval):
            try:
                # Check if any files have been modified
                needs_reload = False

                for file_path in self._properties_files:
                    if os.path.exists(file_path):
                        current_mtime = os.path.getmtime(file_path)
                        if file_path not in self._file_timestamps or \
                                self._file_timestamps[file_path] < current_mtime:
                            needs_reload = True
                            break

                if needs_reload:
                    self._load_properties()

            except Exception as e:
                print(f"Error in auto-reload: {e}")

    def set(self, key: str, value: Any) -> None:
        """Set a property at runtime (overrides files until the next reload)."""
        with self._properties_lock:
            self._properties[key] = str(value)
    
    def get(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """
        Get a property value by key

        Precedence order (highest to lowest):
        1. Command line arguments (--key=value)
        2. Environment variables
        3. Property files (rightmost file has highest precedence)

        Args:
            key: Property key
            default_value: Default value if key not found

        Returns:
            Property value or default_value
        """
        with self._properties_lock:
            return self._properties.get(key, default_value)

    def get_source(self, key: str) -> Optional[str]:
        """
        Get the source of a property value

        Args:
            key: Property key

        Returns:
            Source of the property value: "commandline", "env", "file", or None if not found
        """
        with self._properties_lock:
            return self._property_sources.get(key)

    def get_system_name(self) -> Optional[str]:
        """
        Get the system/application name from 'app.name' property

        Returns:
            Value of 'app.name' property or None if not found
        """
        return self.get('app.name')

    def get_int(self, key: str, default_value: Optional[int] = None) -> Optional[int]:
        """
        Get a property value as integer

        Args:
            key: Property key
            default_value: Default value if key not found

        Returns:
            Property value as int or default_value
        """
        value = self.get(key)
        if value is None:
            return default_value

        try:
            return int(value)
        except (ValueError, TypeError):
            return default_value

    def get_float(self, key: str, default_value: Optional[float] = None) -> Optional[float]:
        """
        Get a property value as float

        Args:
            key: Property key
            default_value: Default value if key not found

        Returns:
            Property value as float or default_value
        """
        value = self.get(key)
        if value is None:
            return default_value

        try:
            return float(value)
        except (ValueError, TypeError):
            return default_value

    def get_bool(self, key: str, default_value: Optional[bool] = None) -> Optional[bool]:
        """
        Get a property value as boolean

        Recognizes the following as True (case-insensitive):
        - true, yes, on, 1, y, t

        Recognizes the following as False (case-insensitive):
        - false, no, off, 0, n, f

        Args:
            key: Property key
            default_value: Default value if key not found or cannot be converted

        Returns:
            Property value as bool or default_value
        """
        value = self.get(key)
        if value is None:
            return default_value

        # Handle boolean values
        if isinstance(value, bool):
            return value

        # Handle string values (case-insensitive)
        if isinstance(value, str):
            value_lower = value.lower().strip()

            # True values
            if value_lower in ('true', 'yes', 'on', '1', 'y', 't'):
                return True

            # False values
            if value_lower in ('false', 'no', 'off', '0', 'n', 'f'):
                return False

        # If value is numeric, use Python's bool conversion
        try:
            num_value = float(value)
            return bool(num_value)
        except (ValueError, TypeError):
            pass

        # Cannot convert, return default
        return default_value

    def get_list(self, key: str, delim: str = ',') -> Optional[List[str]]:
        """
        Get a property value as list by splitting with delimiter

        Args:
            key: Property key
            delim: Delimiter for splitting (default: ',')

        Returns:
            List of strings or None
        """
        value = self.get(key)
        if value is None:
            return None

        return [item.strip() for item in value.split(delim) if item.strip()]

    def get_int_list(self, key: str, delim: str = ',') -> Optional[List[int]]:
        """
        Get a property value as list of integers

        Args:
            key: Property key
            delim: Delimiter for splitting (default: ',')

        Returns:
            List of integers or None
        """
        str_list = self.get_list(key, delim)
        if str_list is None:
            return None

        result = []
        for item in str_list:
            try:
                result.append(int(item))
            except (ValueError, TypeError):
                continue  # Skip invalid integers

        return result if result else None

    def get_float_list(self, key: str, delim: str = ',') -> Optional[List[float]]:
        """
        Get a property value as list of floats

        Args:
            key: Property key
            delim: Delimiter for splitting (default: ',')

        Returns:
            List of floats or None
        """
        str_list = self.get_list(key, delim)
        if str_list is None:
            return None

        result = []
        for item in str_list:
            try:
                result.append(float(item))
            except (ValueError, TypeError):
                continue  # Skip invalid floats

        return result if result else None

    def get_values_by_pattern(self, pattern: str) -> List[str]:
        """
        Get all property values whose keys match the given regex pattern

        Args:
            pattern: Regex pattern to match against property keys

        Returns:
            List of property values for matching keys (empty list if no matches)
        """
        with self._properties_lock:
            try:
                regex = re.compile(pattern)
                matching_values = []

                for key, value in self._properties.items():
                    if regex.match(key):
                        matching_values.append(value)

                return matching_values
            except re.error as e:
                print(f"Invalid regex pattern '{pattern}': {e}")
                return []

    def get_properties_by_pattern(self, pattern: str) -> Dict[str, str]:
        """
        Get all properties (key-value pairs) whose keys match the given regex pattern

        Args:
            pattern: Regex pattern to match against property keys

        Returns:
            Dictionary of matching properties (empty dict if no matches)
        """
        with self._properties_lock:
            try:
                regex = re.compile(pattern)
                matching_properties = {}

                for key, value in self._properties.items():
                    if regex.match(key):
                        matching_properties[key] = value

                return matching_properties
            except re.error as e:
                print(f"Invalid regex pattern '{pattern}': {e}")
                return {}

    def get_all_properties(self) -> Dict[str, str]:
        """
        Get all properties

        Returns:
            Dictionary of all properties
        """
        with self._properties_lock:
            return self._properties.copy()

    def get_all_sources(self) -> Dict[str, str]:
        """
        Get sources for all properties

        Returns:
            Dictionary mapping property keys to their sources
        """
        with self._properties_lock:
            return self._property_sources.copy()

    def resolve_string_content(self, content: str) -> str:
        """
        Resolve ${prop_name} patterns in the given string content.
        Uses the same prioritization logic: commandline > env > file.
        Supports nested patterns and multiple placeholders.
        If a pattern cannot be resolved, it is left as-is.

        Args:
            content: String content with potential ${...} patterns

        Returns:
            Resolved string with all ${...} patterns replaced by property values
        """
        if not content or '${' not in content:
            return content

        with self._properties_lock:
            # Use the existing _resolve_value method with current properties
            # Pass empty visited set for circular reference detection
            return self._resolve_value(content, self._properties, set())

    def load_and_resolve_file_content(self, filename: Union[str, Path]) -> List[str]:
        """
        Load a text file and resolve ${prop_name} patterns in each line.
        Uses the same prioritization logic: commandline > env > file.

        Args:
            filename: Path to the text file to load and resolve

        Returns:
            List of strings representing the resolved file content (one string per line)

        Raises:
            FileNotFoundError: If the file does not exist
            IOError: If there's an error reading the file
        """
        file_path = Path(filename) if not isinstance(filename, Path) else filename

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            resolved_lines = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Don't strip the line to preserve formatting/whitespace
                    # But remove the trailing newline
                    line = line.rstrip('\n\r')
                    resolved_line = self.resolve_string_content(line)
                    resolved_lines.append(resolved_line)

            return resolved_lines

        except Exception as e:
            raise IOError(f"Error reading file {file_path}: {e}")

    def resolve_string_json_content(self, content: str) -> Dict[str, Any]:
        """
        Resolve ${prop_name} patterns in a JSON string and return as dictionary.
        Uses the same prioritization logic: commandline > env > file.

        Args:
            content: JSON string content with potential ${...} patterns

        Returns:
            Dictionary object parsed from the resolved JSON string

        Raises:
            json.JSONDecodeError: If the resolved content is not valid JSON
        """
        resolved_content = self.resolve_string_content(content)

        try:
            return json.loads(resolved_content)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Error parsing resolved JSON content: {e.msg}",
                e.doc,
                e.pos
            )

    def load_and_resolve_json_file_content(self, filename: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a JSON file, resolve ${prop_name} patterns, and return as dictionary.
        Uses the same prioritization logic: commandline > env > file.

        Args:
            filename: Path to the JSON file to load and resolve

        Returns:
            Dictionary object parsed from the resolved JSON file

        Raises:
            FileNotFoundError: If the file does not exist
            IOError: If there's an error reading the file
            json.JSONDecodeError: If the resolved content is not valid JSON
        """
        file_path = Path(filename) if not isinstance(filename, Path) else filename

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return self.resolve_string_json_content(content)

        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Error parsing JSON from file {file_path}: {e.msg}",
                e.doc,
                e.pos
            )
        except Exception as e:
            raise IOError(f"Error reading file {file_path}: {e}")

    def stop_reload(self):
        """Stop the auto-reload thread"""
        self._stop_reload.set()
        if hasattr(self, '_reload_thread'):
            self._reload_thread.join(timeout=5)
```

---

## 5. Data Flow

### 5.1 Calculation Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  CCREngine  │────▶│  Factory    │────▶│ Calculator  │
│   Request   │     │             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                                       │
                           │                                       ▼
                           │                              ┌─────────────┐
                           │                              │   Models    │
                           │                              │ (Trade,Mkt) │
                           │                              └─────────────┘
                           │                                       │
                           ▼                                       ▼
                    ┌─────────────┐                       ┌─────────────┐
                    │   Result    │◀──────────────────────│    Math     │
                    │ Aggregation │                       │ (Simulation)│
                    └─────────────┘                       └─────────────┘
```

### 5.2 CCR Metrics Pipeline

```
Market Data + Trades
        │
        ▼
┌───────────────┐
│ Current Exp.  │───────────────────────────────────────┐
└───────────────┘                                        │
        │                                                │
        ▼                                                │
┌───────────────┐     ┌───────────────┐                 │
│  Path Gen.    │────▶│   Monte       │                 │
│  (Stochastic) │     │   Carlo       │                 │
└───────────────┘     └───────────────┘                 │
        │                    │                          │
        │                    ▼                          │
        │            ┌───────────────┐                  │
        │            │   EE / PFE    │──────────────────┤
        │            └───────────────┘                  │
        │                    │                          │
        ▼                    ▼                          │
┌───────────────┐     ┌───────────────┐                 │
│   PD / LGD    │────▶│     CVA       │◀────────────────┘
└───────────────┘     └───────────────┘
        │                    │
        ▼                    ▼
┌───────────────┐     ┌───────────────┐
│  EAD / EL     │     │   EC / IM     │
└───────────────┘     └───────────────┘
        │                    │
        └────────────┬───────┘
                     ▼
              ┌───────────────┐
              │    RAROC      │
              └───────────────┘
```

---

## 6. Threading Model

### 6.1 Engine Threading Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        CCREngine                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    ThreadPoolExecutor                     │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │  │
│  │  │ Worker 1 │ │ Worker 2 │ │ Worker 3 │ │ Worker N │    │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │  │
│  │       │            │            │            │           │  │
│  │       ▼            ▼            ▼            ▼           │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │               Task Queue (Priority)               │   │  │
│  │  │  [CRITICAL] [HIGH] [NORMAL] [LOW] ...            │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Configuration:                                                │
│  - Default workers: 8                                          │
│  - Configurable via engine.max_workers                         │
│  - Thread name prefix: "ccr_engine"                            │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 Thread Safety Mechanisms

| Mechanism | Usage |
|-----------|-------|
| **Immutable Data** | Calculation inputs are frozen dataclasses |
| **Thread-Local Cache** | Calculator instances cached per-thread |
| **Lock-Free Queues** | Task submission uses concurrent queues |
| **Atomic Statistics** | Engine stats updated with locks |
| **Context Managers** | Automatic cleanup on exit |

---

## 7. Extension Points

### 7.1 Adding a New Calculator

```py
# 1. Create calculator in calculator/python/new_metric_calculator.py
from ..base import BaseCalculator, CalculatorType, CalculationResult

class NewMetricCalculator(BaseCalculator):
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.NEW_METRIC
    
    def _calculate_impl(self, data: Any) -> float:
        # Implementation logic
        return result

# 2. Add to CalculatorType enum in base.py
class CalculatorType(Enum):
    NEW_METRIC = "new_metric"

# 3. Register in factory.py
CALCULATOR_REGISTRY = {
    CalculatorType.NEW_METRIC: {
        'python': NewMetricCalculator,
        'quantlib': QLNewMetricCalculator
    }
}
```

### 7.2 Adding a New Stochastic Process

```py
# 1. Add to ProcessType enum in mathlib/base.py
class ProcessType(Enum):
    NEW_PROCESS = "new_process"

# 2. Implement in path_generator.py
def _generate_new_process(self, params: PathGenerationParams) -> np.ndarray:
    # Implementation
    return paths
```

### 7.3 Adding a New Product

```py
# 1. Create product in products/python/category/new_product.py
@dataclass
class NewProduct(BaseProduct):
    specific_field: float
    
    def calculate_npv(self, market_data: MarketData) -> float:
        # Pricing logic
        return npv
    
    def calculate_ccr_exposure(self) -> CCRExposureProfile:
        # Exposure calculation
        return profile

# 2. Add to __init__.py exports
```

---

## 8. Deployment Considerations

### 8.1 Performance Optimization

| Strategy | Benefit |
|----------|---------|
| Use QuantLib implementation | 2-3x speedup for numerical calculations |
| Increase thread count for I/O | Better parallelism for market data fetching |
| Pre-generate Monte Carlo paths | Amortize simulation cost across portfolio |
| Cache discount factors | Avoid repeated curve interpolation |
| Use NumPy vectorization | 10-100x faster than Python loops |

### 8.2 Scaling Guidelines

| Portfolio Size | Recommended Workers | Expected Time |
|---------------|---------------------|---------------|
| < 1,000 trades | 4 | < 2 seconds |
| 1,000 - 10,000 | 8 | 5-15 seconds |
| 10,000 - 100,000 | 16 | 1-2 minutes |
| > 100,000 | Distributed | Consider partitioning |

### 8.3 Memory Management

- Use streaming for large portfolios
- Clear calculator caches periodically
- Use memory-mapped arrays for massive simulations
- Consider 64-bit Python for > 4GB datasets

---

## Appendix A: Configuration Reference

```properties
# Engine
engine.max_workers=8
engine.default_implementation=python
engine.timeout=300

# Monte Carlo
montecarlo.num_paths=10000
montecarlo.num_steps=252
montecarlo.seed=42
montecarlo.antithetic=true

# Calculators
calculator.confidence_level=0.99
calculator.time_horizon=1.0

# Logging
logging.level=INFO
logging.format=%(asctime)s | %(levelname)-8s | %(name)s | %(message)s
```

---

## Appendix B: Error Handling

| Exception | When Raised |
|-----------|-------------|
| `ConfigurationError` | Invalid configuration file or missing required keys |
| `CalculationError` | Calculation fails (e.g., negative PD) |
| `ModelError` | Invalid model parameters |
| `DataError` | Data validation failures |
| `ValidationError` | Input validation failures |
| `CurveError` | Curve interpolation/construction errors |

---

*Document Version: 2.2.0*  
*Last Updated: December 2025*  
*Copyright © 2025-2030 Ashutosh Sinha. All Rights Reserved.*
