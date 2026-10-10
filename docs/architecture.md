# QLRisk - Architecture Documentation v2.1.0

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
│                           QLRisk v2.1.0                           │
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

```python
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

```python
class PathGeneratorLike(Protocol):
    """Protocol defining path generator interface."""
    
    def generate_paths(
        self,
        params: PathGenerationParams,
        process_type: ProcessType
    ) -> PathResult:
        ...
```

### 4.4 Context Manager Pattern

```python
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

```python
class PropertiesConfigurator:
    """Singleton configuration manager."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
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

```python
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

```python
# 1. Add to ProcessType enum in mathlib/base.py
class ProcessType(Enum):
    NEW_PROCESS = "new_process"

# 2. Implement in path_generator.py
def _generate_new_process(self, params: PathGenerationParams) -> np.ndarray:
    # Implementation
    return paths
```

### 7.3 Adding a New Product

```python
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

*Document Version: 2.1.0*  
*Last Updated: December 2025*  
*Copyright © 2025-2030 Ashutosh Sinha. All Rights Reserved.*
