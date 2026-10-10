# QLRisk - Risk Factors v2.2.1

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the software it describes are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
```

---

## Overview

`qlrisk.riskfactors` is the layer shared by market risk and CCR. It:

1. **Names** every number in a `products.base.MarketData` (`RiskFactorKey`)
2. **Reads and writes** those numbers (`get_factor_value`, `set_factor_value`)
3. **Shocks** market data copy-on-write (`apply_shocks`, curve shapes)
4. **Detects** which factors a product depends on (`BaseProduct.risk_factors()`)
5. **Stores histories** and computes returns (`RiskFactorTimeSeries`)

Everything downstream (sensitivities, VaR/ES scenarios, stress tests and FRTB) is built on these five operations.

---

## 1. Risk Factor Keys

| Key | MarketData location | Risk class | Kind |
|-----|---------------------|------------|------|
| `IR.DISCOUNT.5Y` | `discount_curve[5.0]` | IR | RATE |
| `IR.FWD.SOFR.3M` | `forward_curves["SOFR"][0.25]` | IR | RATE |
| `IR.REF.SOFR` | `reference_rates["SOFR"]` | IR | RATE |
| `FX.EURUSD` | `fx_spots["EURUSD"]` | FX | SPOT |
| `CR.ACME.5Y` | `credit_curves["ACME"][5.0]` | CR | SPREAD |
| `EQ.AAPL` | `equity_prices["AAPL"]` | EQ | PRICE |
| `DIV.AAPL.1Y` | `dividend_curves["AAPL"][1.0]` | EQ | DIVIDEND |
| `BOND.UST10Y` | `bond_prices["UST10Y"]` | CR | PRICE |
| `VOL.swaption_vol` | `volatility_surfaces["swaption_vol"]` (flat) | inferred from name | VOLATILITY |
| `VOL.cap_vol.2Y` | `volatility_surfaces["cap_vol"][2.0]` (term structure) | inferred | VOLATILITY |
| `VOL.eq_vol.1Y.100` | `volatility_surfaces["eq_vol"][1.0][100.0]` (surface) | inferred | VOLATILITY |
| `MISC.sofr_rate` | `market_data.sofr_rate` (ad-hoc attribute) | OT | SCALAR |

Volatility risk classes are inferred from the surface name: `swaption*`, `cap*`, `floor*` and `ir*` map to IR, `fx*` to FX, `eq*`, `stock*` and `index*` to EQ, `cds*` and `credit*` to CR, and `cm*`, `commodity*`, `oil*`, `gas*` and `gold*` to CM.

Tenors are formatted as `3M`, `6M`, `1Y`, `10Y`, or as decimal years (`2.5Y`) when they don't land on a whole month. Keys round-trip through strings:

```python
from qlrisk.riskfactors import RiskFactorKey

key = RiskFactorKey.parse("IR.FWD.SOFR.5Y")
key.field, key.name, key.tenor        # ('forward_curves', 'SOFR', 5.0)
key.risk_class, key.kind              # RiskClass.INTEREST_RATE, FactorKind.RATE
str(key)                              # 'IR.FWD.SOFR.5Y'
```

Names containing `.` (e.g. `BRK.B`) cannot be parsed from text; build such keys directly, e.g. `RiskFactorKey("equity_prices", "BRK.B")`.

> `MarketData` gained three fields in this release: `equity_prices`, `bond_prices` and `reference_rates`. The SFT products already read them; they now default to empty dicts instead of raising `AttributeError`.

---

## 2. Reading, Writing and Enumerating

```python
from qlrisk.data import create_sample_market_data
from qlrisk.riskfactors import (enumerate_risk_factors, get_factor_value,
                                set_factor_value, clone_market_data, RiskClass)

md = create_sample_market_data()

enumerate_risk_factors(md)                                  # all factors, sorted
enumerate_risk_factors(md, risk_classes=[RiskClass.FX])     # FX.EURUSD, FX.GBPUSD, FX.USDJPY
get_factor_value(md, "CR.ACME.5Y")                          # 0.012

clone = clone_market_data(md)                               # independent copy of the shockable fields
set_factor_value(clone, "CR.ACME.5Y", 0.015)                # in place on the clone only
```

---

## 3. Shocks

| Shock type | Formula | Typical use |
|-----------|---------|-------------|
| `ABSOLUTE` | v + s | Rates and spreads (1bp = 0.0001) |
| `RELATIVE` | v × (1 + s) | Prices and spots (s = 0.01 is +1%) |
| `LOG` | v × eˢ | Replaying historical log returns |

```python
from qlrisk.riskfactors import apply_shocks, curve_shocks, parallel, twist, butterfly, ShockType

up1bp   = apply_shocks(md, {"IR.DISCOUNT.5Y": 0.0001})
eq_down = apply_shocks(md, {"EQ.SPX": -0.20, "EQ.AAPL": -0.25}, ShockType.RELATIVE)

# whole-curve shapes (tenor -> size)
steepener = apply_shocks(md, curve_shocks(md, "forward_curves", "SOFR", twist(-0.0025, 0.0025)))
all_ir_up = apply_shocks(md, curve_shocks(md, shape=parallel(0.01), risk_classes=[RiskClass.INTEREST_RATE]))
fly       = apply_shocks(md, curve_shocks(md, "discount_curve", shape=butterfly(0.0, 0.0015)))
```

**Copy-on-write guarantee:** `apply_shocks` never mutates its input. It copies only the fields it shocks; the rest are shared with the base. One base snapshot can therefore serve many threads and scenarios at once.

Shape conventions:

- `twist(short, long, short_tenor=2, long_tenor=10)`: `short` at or below `short_tenor`, `long` at or above `long_tenor`, linear in between.
- `butterfly(wings, belly, 2, 5, 10)`: `wings` at both ends and `belly` at the 5Y point, linear in between.

---

## 4. Curve Interpolation

Products read every curve through `products.base.curve_value(curve, t, default)`, which interpolates linearly between pillars and extrapolates flat outside them.

> **Fix in this release.** Products previously read curves with `curve.get(t, 0.05)`, an exact-key lookup that almost never matched a pillar. Most prices therefore used a flat 5% regardless of the curve. For a 10mm 5Y payer swap, a +100bp curve shift moved the PV by about $2k instead of about $440k. All 87 affected product modules now interpolate. As a result, **PVs and CCR exposures of curve-dependent products change**: they now reflect the market data supplied.

Because interpolation is linear between pillars, bumping one pillar is a standard triangular key-rate shock.

---

## 5. Dependency Detection

`BaseProduct.risk_factors(market_data)` prices the product once against an access-recording copy of the market data. It returns every factor on each curve or surface the product read, or the specific names it read (e.g. only `FX.EURUSD`, not `FX.GBPUSD`).

```python
from datetime import date
from qlrisk.products.base import Currency
from qlrisk.products.python import InterestRateSwap

d0 = md.valuation_date
swap = InterestRateSwap("IRS-1", d0, d0, date(d0.year + 5, d0.month, min(d0.day, 28)), 10e6, Currency.USD, "CP",
                        fixed_rate=0.043)
print(swap.risk_factors(md))    # IR.DISCOUNT.* and IR.FWD.SOFR.*, nothing else
```

Reading any point on a curve counts as depending on the whole curve, because interpolation uses neighbouring pillars. Products whose code path depends on market levels (barriers, for example) can override `risk_factors()`.

---

## 6. Time Series

`RiskFactorTimeSeries` is an immutable panel of levels (dates × factors). Missing values are `NaN`.

```python
from qlrisk.riskfactors import RiskFactorTimeSeries

from qlrisk.data import MarketHistoryGenerator
hist = MarketHistoryGenerator(seed=1).generate(md, num_days=300)   # or from_snapshots / from_records / from_csv

dates, r = hist.returns(horizon=10, overlapping=True)     # 10-day returns
hist.fill_missing("ffill")                                 # or "interpolate"
hist.proxy("EQ.AAPL", "EQ.SPX", beta=1.2)                  # fill any AAPL gaps from SPX returns x 1.2
yesterday = hist.market_data_at(hist.dates[-2], md)        # levels -> MarketData
replayed = apply_shocks(yesterday, hist.return_shocks(r[-1]))
hist.to_csv("history.csv")
```

Default return conventions (override per factor with `return_types=`):

| Factor kind | Return | Formula |
|-------------|--------|---------|
| RATE, SPREAD, DIVIDEND, SCALAR | Absolute | x[t+h] − x[t] |
| SPOT, PRICE, VOLATILITY | Log | ln(x[t+h] / x[t]) |

### Synthetic histories

`qlrisk.data.MarketHistoryGenerator` produces correlated, fat-tailed histories that **end exactly at a given snapshot**, with an optional stress regime:

```python
from qlrisk.data import create_sample_market_data, MarketHistoryGenerator

md = create_sample_market_data()
hist = MarketHistoryGenerator(seed=7).generate(md, num_days=750, stress_start=300, stress_days=60)
```

The model has four layers: a global factor (equities and rates fall, spreads and vols rise in a sell-off), a risk-class factor, a curve factor (adjacent pillars correlate at about 0.93) and idiosyncratic noise. All draws are Student-t with 5 degrees of freedom. Spreads and dividend yields are simulated in log space so they stay positive. Inside the stress window, volatility is scaled up 3× and the global factor drifts down.

---

## API Summary

| Function / class | Purpose |
|------------------|---------|
| `RiskFactorKey`, `RiskClass`, `FactorKind` | Factor naming and classification |
| `enumerate_risk_factors(md, risk_classes=, fields=)` | List factors |
| `get_factor_value` / `set_factor_value` | Read / write (write in place: use on a clone) |
| `clone_market_data(md, fields=)` | Copy-on-write clone |
| `apply_shocks(md, shocks, shock_type=)` | Shocked copy |
| `set_factors(md, levels)` | Copy with factors set to absolute levels |
| `curve_shocks(md, field, name, shape, ...)` | Whole-curve shocks from a shape |
| `parallel`, `twist`, `butterfly` | Curve shapes |
| `detect_risk_factors(product, md)` | Dependency detection (default for `BaseProduct.risk_factors`) |
| `RiskFactorTimeSeries` | Histories, returns, gaps, proxies, CSV |
| `create_sample_market_data`, `MarketHistoryGenerator` | Demo/test data (`qlrisk.data`) |

---

*QLRisk v2.2.1 — Every risk. One engine. | Copyright © 2025-2030 Ashutosh Sinha*
