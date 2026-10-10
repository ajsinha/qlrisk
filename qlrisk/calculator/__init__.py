"""
QLRisk - Calculator Module v2.0.1
================================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.

---

Credit risk calculators with dual Python and QuantLib implementations.

Calculator Types (16):
- Credit Risk: PD, LGD, EAD, EL
- Exposure: CE, PFE, EE, EEE, PEAK_EXPOSURE, STRESSED_EXPOSURE
- Valuation: CVA (+ DVA, FVA, KVA, MVA via xva_calculators)
- Capital: EC, RAROC, IM
- Pricing: MTM, NPV

Implementations:
- Python (14 calculators): Pure Python with NumPy/SciPy
- QuantLib (12 calculators): High-performance C++ backend

Additional Calculators:
- SA-CCR: Basel III/IV Standardized Approach
- XVA Suite: DVA, FVA, KVA, MVA, ColVA
"""

__version__ = "2.0.1"

from .base import (
    BaseCalculator,
    CalculatorType,
    CalculationResult,
    ImplementationType,
    ExposureCalculator,
    CreditRiskCalculator,
    PricingCalculator,
)
from .factory import CalculatorFactory

__all__ = [
    "__version__",
    "BaseCalculator",
    "CalculatorType",
    "CalculationResult",
    "ImplementationType",
    "ExposureCalculator",
    "CreditRiskCalculator",
    "PricingCalculator",
    "CalculatorFactory",
]
