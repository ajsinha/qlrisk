# VaR and Expected Shortfall

```
Copyright © 2025-2030, All Rights Reserved — Ashutosh Sinha | ajsinha@gmail.com
```

> Every `python` block in this guide is executed by `tests/test_doc_examples.py`, top to bottom, in one namespace.

## Setup: a book and a history

```python
from datetime import date
from qlrisk.data import create_sample_market_data, MarketHistoryGenerator
from qlrisk.products.base import Currency
import qlrisk.products.python as P

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
history = MarketHistoryGenerator(seed=7).generate(md, num_days=750, stress_start=300, stress_days=60)

book = [
    P.InterestRateSwap("IRS-10Y", d0, d0, date(2036, 10, 9), 25e6, Currency.USD, "RATES", fixed_rate=0.043),
    P.CorporateBond("ACME-31", d0, d0, date(2031, 10, 9), 10e6, Currency.USD, "CREDIT", coupon=0.05, issuer="ACME"),
    P.FXOption("EURUSD-C", d0, d0, date(2027, 10, 9), 10e6, Currency.EUR, "FX", pair="EURUSD", strike=1.12),
    P.EquityOption("SPX-P", d0, d0, date(2027, 4, 9), 5e6, Currency.USD, "EQUITY", ticker="SPX", strike=5000.0, is_call=False),
]
```

In real use, build `history` from your own data with `RiskFactorTimeSeries.from_snapshots(...)` or `from_csv(...)`.

## Historical VaR and ES (full revaluation)

```python
from qlrisk.engine import MarketRiskEngine, TAYLOR
from qlrisk.scenarios import historical_scenarios

engine = MarketRiskEngine(reporting_currency="USD")
scen = historical_scenarios(history, lookback=250)          # last 250 one-day moves
pnl = engine.scenario_pnl(book, md, scen)                    # trades x scenarios

var99 = pnl.var(0.99)
es975 = pnl.es(0.975)
print(var99)
print(es975)
print("worst days:", var99.tail_scenarios[:3])
```

## Who contributes? Component, incremental and standalone risk

```python
print({k: round(v) for k, v in es975.contributions.items()})        # Euler: sums to ES
print({k: round(v) for k, v in pnl.incremental(0.99).items()})       # VaR change if the trade is removed
print({k: round(v) for k, v in pnl.standalone(0.99).items()})        # each trade on its own

desks = {"IRS-10Y": "Rates", "ACME-31": "Credit", "EURUSD-C": "FX", "SPX-P": "Equity"}
print(pnl.group(desks).var(0.99).contributions)
```

## Holding periods

```python
ten_day_overlap = historical_scenarios(history, lookback=250, horizon=10)                     # 10-day returns
ten_day_sqrt = historical_scenarios(history, lookback=250, horizon=10, sqrt_scaling=True)     # 1-day x sqrt(10)
print(engine.var(book, md, ten_day_overlap).value, engine.var(book, md, ten_day_sqrt).value)
```

## Other scenario methods

```python
from qlrisk.scenarios import filtered_historical_scenarios, monte_carlo_scenarios

aged = historical_scenarios(history, lookback=500, age_weighting=0.99)      # BRW: recent days weigh more
fhs = filtered_historical_scenarios(history, ewma_lambda=0.94, lookback=250) # vol-rescaled to today
mc = monte_carlo_scenarios(history, n=5000, lookback=250, distribution="t", dof=5, seed=1)

for name, s in [("age-weighted", aged), ("filtered", fhs), ("monte carlo (taylor)", mc)]:
    method = TAYLOR if s is mc else "full"
    print(f"{name:22} {engine.var(book, md, s, 0.99, method=method).value:>12,.0f}")
```

`TAYLOR` revalues with delta-gamma sensitivities instead of full repricing. That is much faster for large
scenario sets and accurate for near-linear books.

## Parametric (delta-normal) VaR

```python
pvar = engine.parametric_var(book, md, history, confidence=0.99, lookback=250)
pes = engine.parametric_var(book, md, history, confidence=0.975, lookback=250, measure="es")
ewma = engine.parametric_var(book, md, history, lookback=250, ewma_lambda=0.94)
print(pvar, "\n", pes, "\n", ewma)
print({k: round(v) for k, v in pvar.contributions.items()})
```

## Stressed VaR

```python
svar = engine.stressed_var(book, md, history, window=250, confidence=0.99, horizon_days=10)
print(svar, svar.metadata["window_start"], "->", svar.metadata["window_end"])
```

The search slides a 250-day window over the history (using Taylor P&L) and keeps the window with the
highest VaR. It then fully revalues the portfolio on that window, scaled by √10.

## Hypothetical scenarios

```python
from qlrisk.scenarios import ScenarioSet
from qlrisk.riskfactors import Shock, ShockType

stress = ScenarioSet.from_shocks({
    "equity crash": [Shock("EQ.SPX", -0.25, ShockType.RELATIVE), Shock("VOL.eq_vol.6M", 0.15)],
    "rates +200bp": [Shock(f"IR.FWD.SOFR.{t}", 0.02) for t in ("1Y", "2Y", "5Y", "10Y")],
})
print({k: round(v) for k, v in zip(stress.labels, engine.scenario_pnl(book, md, stress).portfolio)})
```

## The daily pack in one call

```python
for name, result in engine.summary(book, md, history).items():
    print(f"{name:22} {result.value:>14,.0f}")
```

Methodology and formulas: [market_risk/var_es.md](../../market_risk/var_es.md).
