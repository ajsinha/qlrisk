# Backtesting, P&L Explain and Stress Testing

```
Copyright © 2025-2030, All Rights Reserved — Ashutosh Sinha | ajsinha@gmail.com
```

> Every `python` block in this guide is executed by `tests/test_doc_examples.py`, top to bottom, in one namespace.

```python
from datetime import date
from qlrisk.data import create_sample_market_data, MarketHistoryGenerator
from qlrisk.products.base import Currency
from qlrisk.engine import MarketRiskEngine
import qlrisk.products.python as P

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
history = MarketHistoryGenerator(seed=7).generate(md, num_days=750, stress_start=300, stress_days=60)
book = [
    P.InterestRateSwap("IRS-10Y", d0, d0, date(2036, 10, 9), 25e6, Currency.USD, "RATES", fixed_rate=0.043),
    P.CorporateBond("ACME-31", d0, d0, date(2031, 10, 9), 10e6, Currency.USD, "CREDIT", coupon=0.05, issuer="ACME"),
    P.EquityOption("SPX-P", d0, d0, date(2027, 4, 9), 5e6, Currency.USD, "EQUITY", ticker="SPX", strike=5000.0, is_call=False),
]
engine = MarketRiskEngine(reporting_currency="USD")
```

## 1. Backtest VaR and ES

`backtest` rolls a 250-day historical VaR and ES forward over the last `test_days`. It compares each
forecast with the realised hypothetical P&L (full revaluation day over day) and runs every test:

```python
bt = engine.backtest(book, md, history, test_days=250, lookback=250, confidence=0.99)
print(bt["var"].summary())
print("exception dates:", bt["var"].exception_labels)
print("ES backtest:", bt["es"])
print("P&L attribution test:", bt["pla"])
```

On your own series:

```python
import numpy as np
from qlrisk.backtesting import backtest_var, backtest_es, traffic_light, basel_multiplier

pnl = np.random.default_rng(0).standard_normal(500) * 1e5
var_forecast = np.full(500, 2.0e5)                  # a too-small VaR (true 99% VaR is 2.33e5)
res = backtest_var(pnl, var_forecast, 0.99)
print(res.summary(), "| passes:", res.passes())
print([traffic_light(k) for k in (3, 6, 11)], basel_multiplier(6))
```

## 2. Explain yesterday's P&L

```python
yesterday = history.market_data_at(history.dates[-2], md)
today = history.market_data_at(history.dates[-1], md)
explain = engine.explain(book, yesterday, today)
print({k: round(v) for k, v in explain.total().items()})
for trade_id, t in explain.trades.items():
    print(f"{trade_id:8} actual {t.actual:>10,.0f}  theta {t.theta:>9,.0f}  "
          f"{ {k: round(v) for k, v in t.by_risk_class.items()} }  unexplained {t.unexplained:,.0f}")
```

## 3. FRTB P&L attribution test

```python
from qlrisk.pnl import pla_test
series = bt["series"]
print(pla_test(series["hpl"], series["rtpl"]))       # Spearman > 0.80 and KS < 0.09 -> green
```

## 4. Historical stress library

```python
from qlrisk.scenarios import STRESS_LIBRARY
for name, pnl in engine.stress_test(book, md).items():
    print(f"{name:22} {STRESS_LIBRARY[name].description:38} {pnl:>14,.0f}")
```

Add your own scenarios:

```python
from qlrisk.scenarios import StressDefinition, stress_shocks, ScenarioSet
mine = StressDefinition("my_stagflation", "Rates up, equities down", equity=-0.15, vol=0.5,
                        rates=(0.015, 0.025), credit=0.5, fx_usd=0.05, commodity=0.30)
custom = ScenarioSet.from_shocks({mine.name: stress_shocks(md, mine)})
print(engine.stress_test(book, md, custom))
```

## 5. Reverse stress test

What is the most plausible move that loses $2m?

```python
rs = engine.reverse_stress(book, md, history, loss=2_000_000)
print(f"achieved {rs.achieved_loss:,.0f} at {rs.sigma_distance:.1f} sigma (scale {rs.scale:.2f})")
for factor, z in list(rs.top_moves.items())[:5]:
    print(f"  {str(factor):18} {z:+.1f} sd")
```

## 6. Liquidity-adjusted VaR

```python
from qlrisk.calculator.python.liquidity_var import liquidity_adjusted_var
from qlrisk.scenarios import historical_scenarios
var_1d = engine.var(book, md, historical_scenarios(history, lookback=250)).value
positions = {t.trade_id: t.price(md).npv for t in book}
spreads = {"IRS-10Y": 0.0005, "ACME-31": 0.004, "SPX-P": 0.01}
print(round(var_1d), "->", round(liquidity_adjusted_var(var_1d, positions, spreads, liquidity_horizon_days=10)))
```

Methodology: [market_risk/validation.md](../../market_risk/validation.md).
