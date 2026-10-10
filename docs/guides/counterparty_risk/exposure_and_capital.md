# Counterparty Exposure, SA-CCR and CCR Metrics

```
Copyright © 2025-2030, All Rights Reserved — Ashutosh Sinha | ajsinha@gmail.com
```

> Every `python` block in this guide is executed by `tests/test_doc_examples.py`, top to bottom, in one namespace.

## Trade-level exposure profiles and SA-CCR

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
import qlrisk.products.python as P

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
netting_set = [
    P.InterestRateSwap("IRS-1", d0, d0, date(2033, 10, 9), 20e6, Currency.USD, "BANK-A", fixed_rate=0.040),
    P.InterestRateSwap("IRS-2", d0, d0, date(2029, 10, 9), 15e6, Currency.USD, "BANK-A", fixed_rate=0.045, is_payer=False),
    P.FXForward("FXF-1", d0, date(2027, 10, 9), Currency.EUR, Currency.USD, 10e6, 1.07, "BANK-A"),
]
for t in netting_set:
    prof = t.calculate_ccr_exposure(md, time_horizon=5.0, num_scenarios=2000)
    sa = t.calculate_saccr(md)
    print(f"{t.trade_id:6} MtM {t.price(md).npv:>12,.0f}  EPE {prof.epe:>11,.0f}  peak PFE {prof.peak_exposure:>12,.0f}  SA-CCR EAD {sa.ead:>12,.0f}")
```

## Credit metrics through the engine

The `CCREngine` runs calculators on a thread pool. Pick the PD model with `calculator_config`:

```python
from qlrisk.engine import CCREngine
from qlrisk.calculator import CalculatorType

with CCREngine() as engine:
    for rating in ("AA", "BBB", "B"):
        pd = engine.calculate(CalculatorType.PD, {"credit_rating": rating},
                              calculator_config={"model": "transition_matrix"})
        print(rating, f"{pd.value:.4%}")
```

## Full CCR pipeline for one trade

```python
with CCREngine() as engine:
    metrics = engine.calculate_ccr_metrics({
        "trade_id": "T-1", "notional": 25e6, "mtm": 500_000, "maturity": 7.0, "volatility": 0.25,
        "counterparty_pd": 0.015, "counterparty_lgd": 0.5, "rating": "A", "discount_rate": 0.045,
        "recovery_rate": 0.45, "confidence_level": 0.99, "time_horizon": 1.0, "spread": 0.012,
    })
for k in ("pd", "lgd", "ead", "el", "pfe", "cva", "economic_capital", "raroc"):
    v = metrics.get(k)
    print(k, v if v is None or isinstance(v, str) else round(v, 4))
```

Supply `counterparty_pd` / `counterparty_lgd` to use your own estimates; otherwise PD comes from the
`rating` (transition-matrix table) and LGD from `1 - recovery_rate`. RAROC uses `revenue` (default
`spread x notional`) less expected loss over economic capital.

## Wrong-way style check: exposure under stress

```python
from qlrisk.riskfactors import apply_shocks, curve_shocks, parallel, RiskClass
stressed = apply_shocks(md, curve_shocks(md, shape=parallel(-0.015), risk_classes=[RiskClass.INTEREST_RATE]))
for t in netting_set[:2]:
    print(t.trade_id, "MtM base", round(t.price(md).npv), "-> rates -150bp", round(t.price(stressed).npv))
```

Methodology: [SA-CCR](../../saccr.md), [PFE](../../metrics/pfe.md), [CVA](../../metrics/cva.md).
