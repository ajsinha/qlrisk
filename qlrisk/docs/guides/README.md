# QLRisk User Guides

Task-oriented guides. Every `python` example is executed by the test suite (`tests/test_doc_examples.py`),
so examples always match the code.

| Folder | Guide | You will learn |
|--------|-------|----------------|
| `getting_started/` | [Installation](getting_started/installation.md) | Install from source or wheel, verify, CLI |
| | [Your first portfolio](getting_started/first_portfolio.md) | Price, stress, sensitivities and exposure end to end |
| `market_data/` | [Building market data](market_data/building_market_data.md) | `MarketData` fields, conventions, risk-factor view |
| | [Shocks and scenarios](market_data/shocks_and_scenarios.md) | Factor shocks, curve twists, a scenario library |
| | [Historical data](market_data/historical_data.md) | Histories, returns, historical-simulation P&L, CSV, proxies |
| `pricing/` | [Pricing products](pricing/pricing_products.md) | Rates, bonds, FX, equity, credit, commodity, XCCY examples |
| `market_risk/` | [Sensitivity reports](market_risk/sensitivity_reports.md) | Risk by class, ladders, FRTB vertices, gamma, theta, export |
| `counterparty_risk/` | [Exposure and capital](counterparty_risk/exposure_and_capital.md) | Exposure profiles, SA-CCR, PD, full CCR pipeline |

Reference material lives alongside: [architecture](../architecture.md), [market-risk roadmap](../market_risk/README.md),
[calculators](../calculators/README.md), [products](../products/README.md), [models](../models/README.md).
