# QLRisk - Market Risk Roadmap v2.3.1

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the software it describes are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
```

---

> **Every risk. One engine.** This document describes how QLRisk grows from a counterparty-credit-risk
> platform into a unified market-risk + CCR platform, and lists every module that will be built.
> Items marked ✅ have shipped; everything else is **planned** and moves into the main docs as it ships.

| Phase | Status | Docs |
|-------|--------|------|
| 1 — Risk factors and sensitivities | ✅ Delivered | [risk_factors.md](risk_factors.md), [sensitivities.md](sensitivities.md) |
| 1.5 — Real pricers for placeholder products | ✅ Delivered (59 in v2.0, remaining 12 in v2.1) | [pricers.md](pricers.md) |
| 2 — VaR / ES | ✅ Delivered | [var_es.md](var_es.md), [guide](../guides/market_risk/var_and_es.md) |
| 3 — Validation and stress | ✅ Delivered | [validation.md](validation.md), [guide](../guides/market_risk/validation_and_stress.md) |
| 4 — Regulatory capital | ✅ Delivered (SA-CVA, CRE52 netting added in v2.3) | [frtb.md](frtb.md), [guide](../guides/regulatory/capital.md) |
| 5 — One engine | ✅ Delivered | [guide](../guides/reporting/risk_reports.md) |

---

## 1. Design Principle: One Product, One Price, Many Risks

QLRisk already has the hard part of a market-risk system — a large product library with a uniform
`BaseProduct.price(MarketData) -> PricingResult` contract, plus a thread-pooled engine and a calculator
factory. Market risk is, at its core, *repricing that same portfolio under shocked market data*:

```
                        ┌───────────────────────────┐
                        │  products/  (90+ products) │
                        │  price(MarketData)         │
                        └─────────────┬─────────────┘
                                      │ same pricer
          ┌───────────────────────────┼────────────────────────────┐
          ▼                           ▼                            ▼
 Sensitivities                 Market Risk                   CCR & XVA (exists)
 bump 1 factor → reprice       shock all factors per         simulate factors along a
 (Δ, Γ, vega, DV01, CS01)      scenario → reprice → P&L      time grid → reprice → exposure
          │                    → VaR / ES / SVaR              → EE / PFE / CVA
          └──────────────┬────────────┘                            │
                         ▼                                         │
               Regulatory: FRTB SA (sensitivities) ◄── SA-CVA uses CVA sensitivities
                           FRTB IMA (ES)
```

The new layer that unlocks all of this is a **risk-factor abstraction**: a way to name every market
input (`IR.USD.SOFR.5Y`, `FX.EURUSD`, `EQ.AAPL.VOL.1Y.ATM`, …), read it from `MarketData`, and write a
shocked value back. Everything else is built on top.

---

## 2. Modules to Build

New packages are marked **NEW**; changes to existing packages are marked **EXTEND**.

### Phase 1 — Foundation: risk factors, shocks, sensitivities ✅ Delivered

| Module | Status | Contents |
|--------|--------|----------|
| `qlrisk/riskfactors/taxonomy.py` | ✅ NEW | `RiskClass` (IR, CR, EQ, CM, FX, OT), `FactorKind`, `RiskFactorKey` (field, name, tenor, strike) with string form `IR.FWD.SOFR.5Y` and parsing |
| `qlrisk/riskfactors/mapping.py` | ✅ NEW | Enumerate, read and write factors in `products.base.MarketData` (curves, FX, vol flats/terms/surfaces, credit, equity, dividends, bonds, reference rates, ad-hoc attributes); copy-on-write cloning; dependency detection by access recording |
| `qlrisk/riskfactors/shocks.py` | ✅ NEW | Absolute / relative / log shocks; `apply_shocks()` (copy-on-write); `parallel`, `twist`, `butterfly` curve shapes; `curve_shocks()` |
| `qlrisk/riskfactors/timeseries.py` | ✅ NEW | `RiskFactorTimeSeries`: returns with per-kind conventions, horizons, gap filling, proxying, CSV, conversion back to `MarketData` |
| `qlrisk/sensitivities/engine.py` | ✅ NEW | `SensitivityEngine`: central/forward bump-and-reprice, dependency-aware repricing, reporting-currency translation, theta, cross-gamma, optional threads, per-trade error capture |
| `qlrisk/sensitivities/measures.py` | ✅ NEW | DV01, CS01, DIV01, DELTA, VEGA, THETA, CROSS_GAMMA; bump conventions; `Sensitivity` record |
| `qlrisk/sensitivities/results.py` | ✅ NEW | `SensitivityResult`: filtering, aggregation, ladders, export, merge |
| `qlrisk/sensitivities/ladders.py` | ✅ NEW | Tenor ladders; linear re-bucketing onto standard and FRTB vertices |
| `qlrisk/products/base.py` | ✅ EXTEND | `curve_value()` interpolation; `BaseProduct.risk_factors()`; `MarketData.equity_prices / bond_prices / reference_rates` |
| `qlrisk/products/python/**` | ✅ FIX | 87 modules now interpolate curves instead of exact-key lookups that fell back to 5%; `FXForward` / `FXSwap` report PV in the quote currency they are computed in |
| `qlrisk/data/market_history.py` | ✅ NEW | `create_sample_market_data()`; `MarketHistoryGenerator` (correlated fat-tailed histories with a stress regime, ending at a snapshot) |
| `tests/` | ✅ NEW | 68 pytest tests, incl. closed-form checks of DV01, convexity, Black-Scholes delta/gamma/vega, FX delta and theta |

### Phase 2 — VaR and Expected Shortfall ✅ Delivered

As built: `scenarios/{scenario_set, generators, stressed_period}.py`, `pnl/{matrix, revaluation, taylor}.py`,
`calculator/python/var_calculators.py` (pure VaR/ES functions + `VAR` / `EXPECTED_SHORTFALL` calculators;
decomposition lives on `PnLMatrix`), `models/risk_measure.py` (`RiskMeasureResult`),
`engine/market_risk_engine.py`. QuantLib variants were not needed: pricing inside revaluation already
uses each product's own (QuantLib where applicable) pricer. Original plan:

| Module | Status | Contents |
|--------|--------|----------|
| `qlrisk/scenarios/__init__.py` | NEW | Public API |
| `qlrisk/scenarios/historical.py` | NEW | Historical scenario generation from `RiskFactorTimeSeries` (overlapping/non-overlapping, 1d → 10d scaling) |
| `qlrisk/scenarios/filtered_historical.py` | NEW | Volatility-scaled (EWMA / GARCH(1,1)) filtered historical simulation, age-weighted (BRW) weights |
| `qlrisk/scenarios/monte_carlo.py` | NEW | Covariance (EWMA / sample / shrinkage) and Gaussian or Student-t copula scenarios; reuses `mathlib` path generators and Cholesky |
| `qlrisk/scenarios/stressed_period.py` | NEW | Search for the 12-month stress window that maximises portfolio VaR/ES (for SVaR and FRTB reduced-set calibration) |
| `qlrisk/pnl/__init__.py` | NEW | Public API |
| `qlrisk/pnl/revaluation.py` | NEW | Full-revaluation P&L vectors: portfolio × scenarios, batched over the engine thread pool |
| `qlrisk/pnl/taylor.py` | NEW | Sensitivity-based P&L (delta / delta-gamma / delta-gamma-vega) as a fast approximation and a cross-check |
| `qlrisk/models/risk_measure.py` | NEW | `PnLVector`, `VaRResult`, `ESResult`, `RiskContribution` dataclasses (following `models/base.py` conventions) |
| `qlrisk/calculator/python/var_calculators.py` | NEW | `HistoricalVaRCalculator`, `ParametricVaRCalculator` (delta-normal, delta-gamma Cornish-Fisher), `MonteCarloVaRCalculator`, `StressedVaRCalculator` |
| `qlrisk/calculator/python/es_calculator.py` | NEW | `ExpectedShortfallCalculator` (historical, parametric, MC; 97.5% default) |
| `qlrisk/calculator/python/var_decomposition.py` | NEW | Marginal, component (Euler) and incremental VaR/ES by trade, book or risk factor |
| `qlrisk/calculator/qlib/var_calculators.py` | NEW | QuantLib-backed variants where QuantLib adds value (QuantLib pricers inside revaluation, QuantLib statistics/distributions) |
| `qlrisk/calculator/base.py` | EXTEND | New `CalculatorType` members: `VAR_HISTORICAL`, `VAR_PARAMETRIC`, `VAR_MONTE_CARLO`, `STRESSED_VAR`, `EXPECTED_SHORTFALL`, `COMPONENT_VAR`, `MARGINAL_VAR`, `INCREMENTAL_VAR`, `SENSITIVITY`; new `MarketRiskCalculator` base class |
| `qlrisk/calculator/factory.py` | EXTEND | Register the above for both implementations; `get_var_calculator()`, `get_es_calculator()` helpers |
| `qlrisk/engine/market_risk_engine.py` | NEW | `MarketRiskEngine`: `run_sensitivities()`, `run_var()`, `run_es()`, `run_svar()` over a `Portfolio` + `MarketData` + scenario set |

### Phase 3 — Validation, attribution and stress testing ✅ Delivered

As built: `backtesting/{var_backtest, es_backtest}.py`, `pnl/attribution.py` (P&L explain + PLA test),
`scenarios/{stress_library, reverse_stress}.py`, `calculator/python/liquidity_var.py`, and
`MarketRiskEngine.backtest / stress_test / reverse_stress / explain`. Stress P&L runs through the engine
rather than the CCR `stress_calculators.py`. Original plan:

| Module | Status | Contents |
|--------|--------|----------|
| `qlrisk/backtesting/__init__.py` | NEW | Public API |
| `qlrisk/backtesting/var_backtest.py` | NEW | Exception counting, Kupiec POF, Christoffersen independence and conditional coverage, Basel traffic-light zones and multiplier add-on |
| `qlrisk/backtesting/es_backtest.py` | NEW | Acerbi-Székely Z1/Z2 tests, Du-Escanciano tests |
| `qlrisk/pnl/attribution.py` | NEW | P&L explain: actual vs hypothetical vs risk-theoretical P&L; per-factor attribution with unexplained residual |
| `qlrisk/pnl/pla.py` | NEW | FRTB P&L Attribution test (Spearman correlation, Kolmogorov-Smirnov), green/amber/red desk zones |
| `qlrisk/scenarios/stress_library.py` | NEW | Named historical stress scenarios: 1987 crash, 1998 LTCM, 2008 GFC (Lehman), 2010 euro crisis, 2013 taper tantrum, 2016 Brexit, 2020 COVID, 2022 rates shock, 2023 regional-bank stress |
| `qlrisk/scenarios/hypothetical.py` | NEW | User-defined scenario builder (per-factor and per-risk-class shocks), reusing `models/scenario.py` `Scenario`/`CurveShock` |
| `qlrisk/scenarios/reverse_stress.py` | NEW | Reverse stress testing: find the most plausible (Mahalanobis-minimal) shock that breaches a loss threshold |
| `qlrisk/calculator/python/stress_calculators.py` | EXTEND | Market-risk stress P&L alongside the existing stressed-exposure CCR calculators |
| `qlrisk/calculator/python/liquidity_var.py` | NEW | Liquidity-adjusted VaR (exogenous bid-ask spread cost, liquidity-horizon scaling) |

### Phase 4 — Regulatory capital ✅ Delivered (except SA-CVA)

As built: `regulatory/frtb_sa/{parameters, sbm, drc, rrao, capital}.py`, `regulatory/frtb_ima.py`
(single module), `regulatory/basel25.py`, `regulatory/cva_capital.py` (BA-CVA only),
`regulatory/saccr.py`. FRTB results are returned by `frtb_sa_capital()` / `imcc()` rather than new
CalculatorType members. Simplifications are listed in [frtb.md](frtb.md). Original plan:

| Module | Status | Contents |
|--------|--------|----------|
| `qlrisk/regulatory/__init__.py` | NEW | Public API |
| `qlrisk/regulatory/frtb_sa/parameters.py` | NEW | MAR21 risk weights, buckets, intra/inter-bucket correlations for all seven risk classes |
| `qlrisk/regulatory/frtb_sa/sbm.py` | NEW | Sensitivities-based method: delta, vega and curvature charges; weighted sensitivities, bucket aggregation, low/medium/high correlation scenarios |
| `qlrisk/regulatory/frtb_sa/drc.py` | NEW | Default Risk Charge: JTD, maturity scaling, hedge-benefit ratio for non-securitisations, securitisations (non-CTP) and CTP |
| `qlrisk/regulatory/frtb_sa/rrao.py` | NEW | Residual Risk Add-On (exotic underlyings 1.0%, other residual risks 0.1%) |
| `qlrisk/regulatory/frtb_sa/capital.py` | NEW | Total SA capital = SBM + DRC + RRAO, with breakdowns |
| `qlrisk/regulatory/frtb_ima/es_lh.py` | NEW | Liquidity-horizon-adjusted ES (10/20/40/60/120 days), reduced-set stress calibration |
| `qlrisk/regulatory/frtb_ima/nmrf.py` | NEW | Risk-factor eligibility test (modellability) and stressed ES for non-modellable risk factors |
| `qlrisk/regulatory/frtb_ima/capital.py` | NEW | IMCC (constrained/unconstrained), IMA capital with backtesting multiplier, IMA DRC |
| `qlrisk/regulatory/basel25.py` | NEW | Basel 2.5 market-risk capital: max(VaR, m·avg VaR) + max(SVaR, m·avg SVaR) |
| `qlrisk/regulatory/cva_capital.py` | NEW | Basel III CVA risk framework: BA-CVA (reduced/full) and SA-CVA (built on CVA sensitivities from the existing CVA calculator + `SensitivityEngine`) |
| `qlrisk/regulatory/saccr.py` | NEW (re-export) | Re-exports the existing SA-CCR calculator so all regulatory capital lives under one namespace; existing imports keep working |
| `qlrisk/calculator/base.py` | EXTEND | `FRTB_SA`, `FRTB_IMA`, `BASEL25_CAPITAL`, `CVA_CAPITAL` calculator types |

### Phase 5 — Unification, reporting and limits ✅ Delivered

As built: `engine/risk_engine.py` (`RiskEngine.run` / `from_config`; CCREngine and MarketRiskEngine
unchanged and used underneath), `reporting/{hierarchy, report, limits_monitor}.py`,
`scenarios/wrong_way.py`, `demos.py` + `--market-risk` / `--frtb`, `marketrisk.*` config keys,
market-risk members on `models.limit.LimitType` (limit checks reuse `LimitStatus`).

### Backlog (deferred after v2.3.1)

The core platform is complete. These items are deferred until there is a business need:

| # | Item | Size | Scope / trigger |
|---|------|------|-----------------|
| 1 | FRTB securitisation charges | Medium–large | CSR securitisation (non-CTP and CTP) sensitivities and DRC (MAR21, MAR22); needed only if securitisation tranches sit in the trading book |
| 2 | Inflation and cross-currency-basis risk factors | Medium | New `MarketData` fields (inflation curves, basis spreads) → risk factors → FRTB GIRR and SA-CVA inflation factors |
| 3 | SA-CVA refinements | Small | Inflation factors (after #2); explicit groups of legally related counterparties (90% name correlation) |
| 4 | Bond future cheapest-to-deliver | Medium | Deliverable basket, conversion factors, CTD switch and delivery options |
| 5 | Path-dependent MBS prepayment | Medium | Rate-path simulation (burnout, seasonality) replacing the deterministic CPR rule |
| 6 | Convertible call / put features | Medium | Lattice or PDE model with issuer calls, holder puts and credit-equity linkage |

Original plan:

| Module | Status | Contents |
|--------|--------|----------|
| `qlrisk/engine/risk_engine.py` | NEW | `RiskEngine`: single entry point running market-risk, CCR and XVA jobs over a shared scenario/market-data cache. `CCREngine` and `MarketRiskEngine` become thin façades — **existing `CCREngine` code keeps working unchanged** |
| `qlrisk/engine/__init__.py` | EXTEND | Export `RiskEngine`, `MarketRiskEngine`, `CCREngine`, `create_engine()` with a `scope=` argument |
| `qlrisk/reporting/__init__.py` | NEW | Public API |
| `qlrisk/reporting/hierarchy.py` | NEW | Legal entity → desk → book → trade hierarchy; non-additive aggregation for VaR/ES (re-run on the combined P&L vector, not summed) |
| `qlrisk/reporting/report.py` | NEW | Risk report builder: dict / JSON / CSV export of sensitivities, VaR/ES, stress, CCR and capital in one structure |
| `qlrisk/reporting/limits_monitor.py` | NEW | Utilisation and breach checks for VaR, sensitivity and stress limits |
| `qlrisk/models/limit.py` | EXTEND | Market-risk limit types (VaR, ES, DV01, CS01, vega, stress-loss) next to the existing exposure limits |
| `qlrisk/scenarios/wrong_way.py` | NEW | Shared market/credit scenarios linking factor moves to counterparty credit quality — wrong-way risk for CVA/PFE |
| `qlrisk/main.py` | EXTEND | `qlrisk --market-risk` and `qlrisk --frtb` demos next to the existing `--quick`, `--stress` and `--benchmark` |
| `qlrisk/config/application.properties` | EXTEND | `marketrisk.*` keys: VaR confidence, holding period, lookback, ES level, EWMA lambda, scenario type |

---

## 3. Product Pricing (Phase 1.5) ✅

Phase 1 found that 71 of 91 product modules were placeholders (`price()` returned `notional × DF × 1%`).
**59 of them now use market-driven analytic pricers** in `products/python/_pricing.py` (bonds, FRNs,
money market, repo, cash equities and funds, equity options and forwards, FX vanilla / digital /
barrier options and NDFs, CDS and CDS indices, commodity forwards, swaps and options, and
cross-currency swaps). See [pricers.md](pricers.md).

**v2.3.1 completed the set:** IR / bond / VIX futures, variance and dividend swaps, equity swap and TRS,
convertible bond, MBS (rate-dependent prepayment), ABS and CDO / CLO tranches now have compact models too.

## 4. Usage (as delivered)

```python
from qlrisk.demos import demo_book
from qlrisk.engine import MarketRiskEngine, RiskEngine
from qlrisk.scenarios import historical_scenarios

book, md, history, tree, frtb_maps = demo_book()

mre = MarketRiskEngine(reporting_currency="USD")
scen = historical_scenarios(history, lookback=250, horizon=10, sqrt_scaling=True)
print(mre.var(book, md, scen, confidence=0.99), mre.es(book, md, scen, confidence=0.975))
print(mre.sensitivities(book, md).ladder("forward_curves", "SOFR"))

report = RiskEngine(reporting_currency="USD").run(          # one engine, every risk
    book, md, history, measures=("VAR", "ES", "SENSITIVITIES", "EXPOSURE", "FRTB_SA"), frtb=frtb_maps)
print(report)
```

## 5. Documentation That Ships With Each Phase

| Phase | New docs |
|-------|----------|
| 1 ✅ | `market_risk/risk_factors.md`, `market_risk/sensitivities.md` |
| 2 | `calculators/var_calculator.md`, `calculators/es_calculator.md`, `calculators/var_decomposition.md`, `metrics/var.md`, `metrics/expected_shortfall.md`, VaR/ES section in `mathematical_formulas.md` |
| 3 | `market_risk/backtesting.md`, `market_risk/pnl_attribution.md`, `market_risk/stress_testing.md` |
| 4 | `market_risk/frtb_sa.md`, `market_risk/frtb_ima.md`, `market_risk/cva_capital.md` |
| 5 | `architecture.md` updated for `RiskEngine`; `quickstart.md` market-risk walkthrough; reporting guide |

---

## 6. Compatibility Commitments

- No breaking changes to existing imports: `qlrisk.engine.CCREngine`, all calculators, products and models keep their current APIs.
- Every new calculator follows the existing `BaseCalculator` / `CalculatorFactory` pattern with Python and (where useful) QuantLib implementations.
- Shocked market data is always a copy; base `MarketData` is never mutated, so CCR and market-risk runs can share it safely across threads.

---

*QLRisk v2.3.1 — Every risk. One engine. | Copyright © 2025-2030 Ashutosh Sinha*
