# Building Market Data

```
Copyright © 2025-2030, All Rights Reserved — Ashutosh Sinha | ajsinha@gmail.com
```

> Every `python` block in this guide is executed by `tests/test_doc_examples.py`, top to bottom, in one namespace.

Products price against `qlrisk.products.base.MarketData`. Curves are `{tenor_in_years: value}` dicts,
read with linear interpolation and flat extrapolation.

| Field | Shape | Convention | Risk factor |
|-------|-------|-----------|-------------|
| `discount_curve` | `{t: r}` | continuously-compounded zero rate | `IR.DISCOUNT.<t>` |
| `forward_curves` | `{index: {t: r}}` | zero rates per index (SOFR, ESTR, ...) | `IR.FWD.<index>.<t>` |
| `reference_rates` | `{name: r}` | overnight fixings | `IR.REF.<name>` |
| `fx_spots` | `{"EURUSD": 1.08}` | quote ccy per 1 base ccy | `FX.<pair>` |
| `credit_curves` | `{name: {t: s}}` | credit spreads | `CR.<name>.<t>` |
| `equity_prices`, `dividend_curves` | `{ticker: p}`, `{ticker: {t: q}}` | price, dividend yield | `EQ.<ticker>`, `DIV.<ticker>.<t>` |
| `commodity_prices` | `{name: p}` | spot price | `CMDTY.<name>` |
| `bond_prices` | `{id: p}` | clean price | `BOND.<id>` |
| `volatility_surfaces` | `{name: vol}`, `{name: {t: vol}}` or `{name: {t: {k: vol}}}` | Black vols | `VOL.<name>[.<t>[.<k>]]` |

## Build by hand

```python
from datetime import date
from qlrisk.products.base import MarketData, curve_value

md = MarketData(
    valuation_date=date(2026, 10, 9),
    discount_curve={0.5: 0.041, 1.0: 0.040, 5.0: 0.039, 10.0: 0.041},
    forward_curves={"SOFR": {0.5: 0.042, 1.0: 0.041, 5.0: 0.040, 10.0: 0.042}},
    fx_spots={"EURUSD": 1.085},
    credit_curves={"ACME": {1.0: 0.008, 5.0: 0.012}},
    equity_prices={"AAPL": 190.0},
    commodity_prices={"WTI": 78.0},
    volatility_surfaces={"eq_vol": {0.5: 0.22, 1.0: 0.21}, "fx_vol": 0.09, "swaption_vol": 0.20},
)
print(curve_value(md.discount_curve, 3.0))          # interpolated 3y zero rate
```

## Inspect and edit through risk factors

```python
from qlrisk.riskfactors import enumerate_risk_factors, get_factor_value, set_factors, RiskClass

for key in enumerate_risk_factors(md, risk_classes=[RiskClass.CREDIT, RiskClass.FX]):
    print(key, get_factor_value(md, key))

md2 = set_factors(md, {"EQ.AAPL": 200.0, "VOL.fx_vol": 0.11})   # copy with new levels
print(md.equity_prices["AAPL"], "->", md2.equity_prices["AAPL"])
```

## Sample data

`qlrisk.data.create_sample_market_data(valuation_date)` returns a complete multi-asset snapshot
(USD discounting, SOFR/ESTR/SONIA, 3 FX pairs, IR/FX/EQ/commodity vols, 3 credit curves, equities,
dividends, commodities, bonds, fixings). Use it as a template and override what you need.

Next: [Shocks and scenarios](shocks_and_scenarios.md)
