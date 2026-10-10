"""
QLRisk v2.1.0
============================

Unified Market Risk & Counterparty Credit Risk Analytics Platform
"Every risk. One engine."

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This software and associated documentation are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.

Components:
-----------
- products: 81 financial products across 12 asset classes
- calculator: 16 risk calculators (Python & QuantLib implementations)
- models: 55+ domain models for trades, portfolios, counterparties
- core: Configuration, logging, timing, validation utilities
- engine: High-performance multi-threaded risk calculation engine

- riskfactors: Risk-factor keys, market-data shocks and factor histories
- sensitivities: Bump-and-reprice DV01, CS01, delta, gamma, vega, theta, ladders

Further market-risk modules (VaR/ES, stress, backtesting, FRTB) are on the
roadmap; see docs/market_risk/README.md
- mathlib: Mathematical library with 7 stochastic processes
- data: Test data generation and management

Quick Start:
-----------
    from qlrisk.engine import CCREngine
    from qlrisk.calculator import CalculatorType
    
    with CCREngine() as engine:
        result = engine.calculate(CalculatorType.PD, {'credit_rating': 'BBB'},
                                  calculator_config={'model': 'transition_matrix'})
        print(f"PD: {result.value:.4%}")

For more examples, see docs/quickstart.md
"""

__version__ = "2.1.0"
__author__ = "Ashutosh Sinha"
__email__ = "ajsinha@gmail.com"
__copyright__ = "Copyright © 2025-2030, All Rights Reserved"
__license__ = "Proprietary"

# Version info tuple
VERSION = (2, 1, 0)
VERSION_STRING = ".".join(map(str, VERSION))

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__copyright__",
    "__license__",
    "VERSION",
    "VERSION_STRING",
]
