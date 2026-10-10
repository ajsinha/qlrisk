# Shocks and Scenarios

```
Copyright © 2025-2030, All Rights Reserved — Ashutosh Sinha | ajsinha@gmail.com
```

> Every `python` block in this guide is executed by `tests/test_doc_examples.py`, top to bottom, in one namespace.

`apply_shocks` returns a **copy**; the base market data is never modified.

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.riskfactors import apply_shocks, curve_shocks, parallel, twist, butterfly, Shock, ShockType, RiskClass

md = create_sample_market_data(date(2026, 10, 9))
```

## Single-factor shocks

```python
up_1bp = apply_shocks(md, {"IR.FWD.SOFR.5Y": 0.0001})                       # absolute (rates, spreads)
eq_dn  = apply_shocks(md, {"EQ.SPX": -0.10, "EQ.AAPL": -0.15}, ShockType.RELATIVE)
vol_up = apply_shocks(md, [Shock("VOL.eq_vol.1Y", 0.05)])                    # +5 vol points
print(up_1bp.forward_curves["SOFR"][5.0] - md.forward_curves["SOFR"][5.0], eq_dn.equity_prices["SPX"])
```

## Curve shapes

```python
steepener = apply_shocks(md, curve_shocks(md, "forward_curves", "SOFR", twist(-0.0025, 0.0025)))
all_rates = apply_shocks(md, curve_shocks(md, shape=parallel(0.01), risk_classes=[RiskClass.INTEREST_RATE]))
belly     = apply_shocks(md, curve_shocks(md, "discount_curve", shape=butterfly(0.0, 0.0020)))
print({t: round(steepener.forward_curves["SOFR"][t] - r, 5) for t, r in md.forward_curves["SOFR"].items()})
```

## A named scenario library

```python
SCENARIOS = {
    "rates +100bp": curve_shocks(md, shape=parallel(0.01), risk_classes=[RiskClass.INTEREST_RATE]),
    "equity -25%":  [Shock(k, -0.25, ShockType.RELATIVE) for k in ("EQ.SPX", "EQ.AAPL", "EQ.MSFT")],
    "credit +200%": [Shock(k.factor, 2.0, ShockType.RELATIVE)
                     for k in curve_shocks(md, "credit_curves", shape=parallel(0.0))],
    "USD rally":    [Shock("FX.EURUSD", -0.08, ShockType.RELATIVE), Shock("FX.GBPUSD", -0.08, ShockType.RELATIVE)],
}

from qlrisk.products.base import Currency
from qlrisk.products.python import CorporateBond, EquityOption
today = md.valuation_date
book = [CorporateBond("B1", today, today, date(2031, 10, 9), 5e6, Currency.USD, "GLOBEX", coupon=0.05, issuer="GLOBEX"),
        EquityOption("O1", today, today, date(2027, 10, 9), 2e6, Currency.USD, "CP", ticker="SPX")]
base = sum(t.price(md).npv for t in book)
for name, shocks in SCENARIOS.items():
    print(f"{name:13} {sum(t.price(apply_shocks(md, shocks)).npv for t in book) - base:>14,.0f}")
```

Shock types: `ABSOLUTE` (v + s), `RELATIVE` (v × (1 + s)), `LOG` (v × eˢ).

Next: [Historical data](historical_data.md)
