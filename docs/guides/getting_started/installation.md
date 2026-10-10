# Installation and First Run

```
Copyright © 2025-2030, All Rights Reserved — Ashutosh Sinha | ajsinha@gmail.com
```

> Every `python` block in this guide is executed by `tests/test_doc_examples.py`, top to bottom, in one namespace.

## Install

```bash
# from the repository (editable, with dev tools)
pip install -e ".[dev]"

# or from the prebuilt wheel committed in dist/ (use this in other projects)
pip install /path/to/qlrisk/dist/qlrisk-2.0.1-py3-none-any.whl

# dependencies only
pip install -r requirements.txt
```

Requires Python 3.9+, numpy, scipy and QuantLib (installed automatically).

## Verify

```python
import qlrisk
from qlrisk.riskfactors import enumerate_risk_factors
from qlrisk.data import create_sample_market_data

print("qlrisk", qlrisk.__version__)
md = create_sample_market_data()
print(len(enumerate_risk_factors(md)), "risk factors in the sample market")
```

## Command line demos

```bash
qlrisk --quick        # quick CCR demo
qlrisk --stress       # stress testing demo
qlrisk --benchmark    # performance benchmarks
qlrisk --market-risk  # market risk report on a demo book (VaR, ES, SVaR, stress, backtest, limits)
qlrisk --frtb         # FRTB SA capital breakdown
pytest                # run the test suite
```

## Package map

| Package | Use it for |
|---------|-----------|
| `qlrisk.products` | 90+ products with `price()`, `calculate_ccr_exposure()`, `calculate_saccr()` |
| `qlrisk.data` | Sample market data, synthetic histories, test portfolios |
| `qlrisk.riskfactors` | Naming, reading, shocking market data; factor histories |
| `qlrisk.sensitivities` | DV01, CS01, delta, gamma, vega, theta, ladders |
| `qlrisk.engine` | `RiskEngine` (everything), `MarketRiskEngine`, `CCREngine` |
| `qlrisk.scenarios` / `qlrisk.pnl` | Scenario sets, stress library, scenario P&L, P&L explain |
| `qlrisk.backtesting` / `qlrisk.regulatory` | VaR/ES backtests; FRTB SA/IMA, Basel 2.5, BA-CVA |
| `qlrisk.reporting` | Reports, hierarchies, limits |
| `qlrisk.calculator` | Credit / CCR calculators and VaR / ES calculators |

Next: [Your first portfolio](first_portfolio.md).
