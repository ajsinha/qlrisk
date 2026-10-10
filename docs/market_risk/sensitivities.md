# QLRisk - Sensitivities v2.2.0

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the software it describes are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
```

---

## Overview

`qlrisk.sensitivities` computes bump-and-reprice sensitivities for **any** `BaseProduct`: DV01, CS01, delta, gamma, vega, cross-gamma and theta. It also produces tenor ladders, including on FRTB vertices.

For each risk factor, the engine builds the bumped market data **once** and reprices only the trades that depend on that factor. Dependencies are detected automatically through `BaseProduct.risk_factors()`.

```python
from qlrisk.data import create_sample_market_data
from qlrisk.sensitivities import SensitivityEngine, FRTB_GIRR_VERTICES

md = create_sample_market_data()
result = SensitivityEngine().compute(trades, md, reporting_currency="USD", include_theta=True)

result.aggregate(("risk_class", "measure"))          # e.g. {(IR, DV01): 4513.4, (FX, DELTA): 10569.0, ...}
print(result.ladder("forward_curves", "SOFR", vertices=FRTB_GIRR_VERTICES))
result.to_rows()                                      # flat dicts for CSV / pandas
```

---

## 1. Conventions

Every first-order value is the **PV change for an up move of one bump unit**:

| Factor kind | Bump | Measure | Meaning of `value` |
|-------------|------|---------|--------------------|
| RATE | +1bp absolute | `DV01` | PV change per +1bp |
| SPREAD | +1bp absolute | `CS01` | PV change per +1bp |
| DIVIDEND | +1bp absolute | `DIV01` | PV change per +1bp |
| SPOT / PRICE | +1% relative | `DELTA` | PV change per +1% move |
| VOLATILITY | +1 vol point absolute | `VEGA` | PV change per +1 vol point |
| SCALAR | +1bp absolute | `DELTA` | PV change per +1bp |

Each `Sensitivity` record also carries:

- `derivative`: dPV/dx in the factor's natural units. For equity delta this is the share-equivalent delta N(d₁) × quantity.
- `gamma`: with central differences, PV₊ − 2PV₀ + PV₋, the second-order change per bump unit². Natural gamma is `gamma / (bump in factor units)²`.

Sign convention: a payer swap has **positive** DV01, because it gains when rates rise.

### Methods

| Method | Repricings per factor | Outputs |
|--------|-----------------------|---------|
| `central` (default) | 2 | First order (O(h²) accurate) and gamma |
| `forward` | 1 | First order (O(h) accurate) |

Override bump sizes per factor kind:

```python
from qlrisk.sensitivities import BumpSpec
from qlrisk.riskfactors import FactorKind, ShockType

engine = SensitivityEngine(bumps={FactorKind.PRICE: BumpSpec(0.001, ShockType.RELATIVE, "10bp")})
```

---

## 2. Reporting Currency and FX Translation

Without a `reporting_currency`, values are in each trade's pricing currency. With one, every PV, base and bumped, is converted using the **same** market data's FX spots. The direct pair, inverse pair or triangulation through USD is used, whichever is available. FX factors therefore capture translation risk, and the engine adds the conversion's FX pairs to each trade's dependencies automatically.

---

## 3. Theta and Cross-Gamma

- `include_theta=True` adds a `THETA` record per trade: the PV change from rolling the valuation date forward one calendar day with unchanged market data. It includes curve roll-down.
- `engine.cross_gamma(trades, md, factors)` returns `CROSS_GAMMA` records for every pair of factors, using (PV₊₊ − PV₊₋ − PV₋₊ + PV₋₋) / 4 per bumpᵢ × bumpⱼ. It costs 4 repricings per pair, so pass a targeted list. Delta-vol cross-gamma is vanna.

---

## 4. Results

`SensitivityResult` holds `records`, `base_pv`, `currency` and `errors`.

| Method | Returns |
|--------|---------|
| `filter(trade_id=, measure=, risk_class=, factor=)` | Matching records |
| `get(trade_id, factor)` | One first-order record |
| `aggregate(by=, value="value" \| "gamma")` | Sums grouped by any of `trade_id`, `factor`, `risk_class`, `measure`, `field`, `curve`, `tenor` |
| `by_factor()` | Portfolio sensitivity per factor |
| `total(measure=, risk_class=)` | Scalar sum |
| `theta()` | Theta per trade |
| `ladder(field, name, measure=, vertices=)` / `ladders()` | Tenor ladders |
| `to_rows()` | Flat dicts |
| `merge(other)` | Combine books |

**Robustness:** a trade that fails to price is recorded in `errors` (trade, factor and message) and skipped. The run continues.

---

## 5. Tenor Ladders

`ladder()` groups tenored sensitivities by curve. With `vertices=`, each tenor's amount is split linearly between its two neighbouring vertices and amounts outside the range go to the nearest end. Totals are always preserved.

| Constant | Vertices (years) |
|----------|------------------|
| `STANDARD_TENORS` | 1M, 3M, 6M, 1, 2, 3, 5, 7, 10, 15, 20, 30 |
| `FRTB_GIRR_VERTICES` | 0.25, 0.5, 1, 2, 3, 5, 10, 15, 20, 30 |
| `FRTB_CSR_VERTICES` | 0.5, 1, 3, 5, 10 |
| `FRTB_VEGA_MATURITIES` | 0.5, 1, 3, 5, 10 |

```
discount_curve dv01
      3M             -2.48
      6M              1.72
      1Y              2.32
      2Y            -41.44
      5Y          1,942.59
     10Y            492.18
   total          2,394.89
```

---

## 6. Performance

- **Dependency detection** means each bumped market data is priced only by the trades that read that factor. A swap is never repriced for an FX bump.
- **`max_workers`** spreads factors across threads. Pure-Python pricers gain little because of the GIL; QuantLib-backed pricers, which release the GIL, can benefit. The default is 1 (sequential).

---

## 7. Validation

The test suite (`tests/test_sensitivities.py`) checks the engine against closed-form results:

| Check | Tolerance |
|-------|-----------|
| Zero-coupon bond DV01 = −T × PV × 1bp, and its convexity | 0.01% / 1% |
| Black-Scholes delta, gamma and vega for an equity call | 0.1% |
| FX forward delta = N × S × 1% × DF | 1e-6 |
| Sum of key-rate DV01s = full parallel 1bp bump | 0.1% |
| ZCB theta = PV × instantaneous forward / 365.25 | 1% |
| Results identical with and without dependency detection, and with 1 or 4 threads | exact |

---

## 8. Model Coverage

Since v2.2.0 every product prices off market data (see [pricers.md](pricers.md)), so every product has
meaningful sensitivities. Model simplifications are listed in pricers.md.

---

*QLRisk v2.2.0 — Every risk. One engine. | Copyright © 2025-2030 Ashutosh Sinha*
