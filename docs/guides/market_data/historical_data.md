# Historical Data and Returns

```
Copyright © 2025-2030, All Rights Reserved — Ashutosh Sinha | ajsinha@gmail.com
```

> Every `python` block in this guide is executed by `tests/test_doc_examples.py`, top to bottom, in one namespace.

`RiskFactorTimeSeries` stores factor levels by date; `MarketHistoryGenerator` creates realistic synthetic
histories (with an optional stress period) that end exactly at a given snapshot.

```python
from datetime import date
import numpy as np
from qlrisk.data import create_sample_market_data, MarketHistoryGenerator

md = create_sample_market_data(date(2026, 10, 9))
hist = MarketHistoryGenerator(seed=42).generate(md, num_days=500, stress_start=250, stress_days=40)
print(hist)
```

## Returns

Rates/spreads use absolute returns; prices, spots and vols use log returns (override with `return_types=`).

```python
dates, r1 = hist.returns()                       # 1-day
_, r10 = hist.returns(horizon=10)                # 10-day overlapping
spx = hist.column("EQ.SPX")
print("SPX daily vol", r1[:, spx].std().round(4), " 10d vol", r10[:, spx].std().round(4))
```

## Replay history on today's market (historical-simulation P&L)

```python
from qlrisk.riskfactors import apply_shocks
from qlrisk.products.base import Currency
from qlrisk.products.python import EquityOption

opt = EquityOption("O1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 1e6, Currency.USD, "CP", ticker="SPX")
base = opt.price(md).npv
pnl = np.array([opt.price(apply_shocks(md, hist.return_shocks(row))).npv - base for row in r1])
print("1d 99% VaR", round(-np.percentile(pnl, 1)), " worst day", round(pnl.min()))
```

## Gaps, proxies, files

```python
import os, tempfile
from qlrisk.riskfactors import RiskFactorTimeSeries

small = hist.select(["EQ.SPX", "EQ.AAPL"]).window(hist.dates[-5], hist.dates[-1])
path = os.path.join(tempfile.mkdtemp(), "hist.csv")
small.to_csv(path)
loaded = RiskFactorTimeSeries.from_csv(path)
print(loaded.shape, loaded.dates[0])

gappy = RiskFactorTimeSeries(loaded.dates, ["EQ.SPX", "EQ.NEWCO"],
                             np.column_stack([loaded.series("EQ.SPX"), [np.nan, np.nan, 10.0, np.nan, 10.5]]))
print(gappy.proxy("EQ.NEWCO", "EQ.SPX").series("EQ.NEWCO").round(3))
print(gappy.fill_missing("ffill").series("EQ.NEWCO"))
```

Rebuild a full `MarketData` for any historical date with `hist.market_data_at(day, template=md)`.
