"""
QLRisk - QuantLib Calculators v1.3.0
===================================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.

---

QuantLib-based implementations of 12 CCR risk calculators.

Provides high-performance C++ backed calculations when QuantLib is available.
Falls back to Python implementations if QuantLib is not installed.

Available Calculators:
- PDCalculatorQL: Probability of Default
- LGDCalculatorQL: Loss Given Default
- EADCalculatorQL: Exposure at Default
- ELCalculatorQL: Expected Loss
- CECalculatorQL: Current Exposure
- PFECalculatorQL: Potential Future Exposure
- EECalculatorQL: Expected Exposure
- CVACalculatorQL: Credit Valuation Adjustment
- ECCalculatorQL: Economic Capital
- RAROCCalculatorQL: Risk-Adjusted Return on Capital
- IMCalculatorQL: Initial Margin
- StressedExposureCalculatorQL: Stress Testing
"""

__version__ = "1.3.0"

# Check if QuantLib is available
try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False
    import warnings
    warnings.warn(
        "QuantLib not available. Install with: pip install QuantLib-Python",
        ImportWarning
    )

if QUANTLIB_AVAILABLE:
    from .pd_calculator import PDCalculatorQL
    from .lgd_calculator import LGDCalculatorQL
    from .ead_calculator import EADCalculatorQL
    from .el_calculator import QuantLibELCalculator as ELCalculatorQL
    from .ce_calculator import CECalculatorQL
    from .pfe_calculator import PFECalculatorQL
    from .ee_calculator import EECalculatorQL
    from .cva_calculator import CVACalculatorQL
    from .ec_calculator import ECCalculatorQL
    from .raroc_calculator import RAROCCalculatorQL
    from .im_calculator import IMCalculatorQL
    from .stress_calculators import StressedExposureCalculatorQL, PeakExposureCalculatorQL
    
    __all__ = [
        "__version__",
        "QUANTLIB_AVAILABLE",
        "PDCalculatorQL",
        "LGDCalculatorQL",
        "EADCalculatorQL",
        "ELCalculatorQL",
        "CECalculatorQL",
        "PFECalculatorQL",
        "EECalculatorQL",
        "CVACalculatorQL",
        "ECCalculatorQL",
        "RAROCCalculatorQL",
        "IMCalculatorQL",
        "StressedExposureCalculatorQL",
        "PeakExposureCalculatorQL",
    ]
else:
    __all__ = ["__version__", "QUANTLIB_AVAILABLE"]
