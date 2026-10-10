"""
QLRisk - Python Calculators v2.2.1
=================================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.

---

Pure Python implementations of 14 CCR risk calculators.

Credit Risk Calculators:
- PDCalculator: Probability of Default (Merton, rating-based, reduced-form)
- LGDCalculator: Loss Given Default (workout, market-implied)
- EADCalculator: Exposure at Default (current, regulatory)
- ELCalculator: Expected Loss (EL = PD × LGD × EAD)

Exposure Calculators:
- CECalculator: Current Exposure (MTM, collateral-adjusted)
- PFECalculator: Potential Future Exposure (Monte Carlo, parametric)
- EECalculator: Expected Exposure profile generation
- StressedExposureCalculator: Stress testing scenarios
- PeakExposureCalculator: Maximum exposure calculation

Valuation Adjustment Calculators:
- CVACalculator: Credit Valuation Adjustment
- XVA Calculators: DVA, FVA, KVA, MVA, ColVA

Capital Calculators:
- ECCalculator: Economic Capital (Vasicek, Gordy, IRB)
- RAROCCalculator: Risk-Adjusted Return on Capital
- IMCalculator: Initial Margin (ISDA SIMM)

Regulatory Calculators:
- SACCRCalculator: SA-CCR EAD (Basel III/IV)
"""

__version__ = "2.2.1"

from .pd_calculator import PDCalculator
from .lgd_calculator import LGDCalculator
from .ead_calculator import EADCalculator
from .el_calculator import ExpectedLossCalculator as ELCalculator
from .ce_calculator import CurrentExposureCalculator as CECalculator
from .pfe_calculator import PFECalculator
from .ee_calculator import ExpectedExposureCalculator as EECalculator
from .cva_calculator import CVACalculator
from .ec_calculator import EconomicCapitalCalculator as ECCalculator
from .raroc_calculator import RAROCCalculator
from .im_calculator import InitialMarginCalculator as IMCalculator
from .stress_calculators import StressedExposureCalculator, PeakExposureCalculator
from .xva_calculators import DVACalculator, FVACalculator, KVACalculator, MVACalculator
from .saccr_calculator import SACCRCalculator
from .xva_calculators import DVAInput, DVAResult, FVAInput, FVAResult, KVAInput, KVAResult, MVAInput, MVAResult
from .raroc_calculator import RAROCInput
from .saccr_calculator import SACCRInput, SACCRResult
from .el_calculator import ELInput, ELResult
from .cva_calculator import CVAInput
from .ec_calculator import ECInput

__all__ = [
    "__version__",
    # Credit Risk
    "PDCalculator",
    "LGDCalculator",
    "EADCalculator",
    "ELCalculator",
    # Exposure
    "CECalculator",
    "PFECalculator",
    "EECalculator",
    "StressedExposureCalculator",
    "PeakExposureCalculator",
    # Valuation
    "CVACalculator",
    "DVACalculator",
    "FVACalculator",
    "KVACalculator",
    "MVACalculator",
    # Capital
    "ECCalculator",
    "RAROCCalculator",
    "IMCalculator",
    # Regulatory
    "SACCRCalculator",
    "DVAInput", "DVAResult", "FVAInput", "FVAResult", "KVAInput", "KVAResult", "MVAInput", "MVAResult",
    "RAROCInput", "SACCRInput", "SACCRResult", "ELInput", "ELResult", "CVAInput", "ECInput",
]
