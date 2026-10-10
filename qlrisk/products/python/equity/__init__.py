"""
QLRisk - Equity Derivative Products v2.2.1
=========================================================

Equity derivative products including swaps, options, forwards, and total return swaps.

Products:
- EquitySwap: Equity swap
- EquityOption: Equity/stock options
- EquityForward: Equity forwards
- VarianceSwap: Variance swaps
- DividendSwap: Dividend swaps
- EquityTRS: Equity Total Return Swap

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

__version__ = "2.2.1"

from .equity_swap import EquitySwap
from .equity_option import EquityOption
from .equity_forward import EquityForward
from .variance_swap import VarianceSwap
from .dividend_swap import DividendSwap
from .equity_trs import EquityTRS, EquityTRSType, EquityTRSTerms, TRSReturnType, TRSResetType

__all__ = [
    "__version__",
    "EquitySwap",
    "EquityOption",
    "EquityForward",
    "VarianceSwap",
    "DividendSwap",
    "EquityTRS",
    "EquityTRSType",
    "EquityTRSTerms",
    "TRSReturnType",
    "TRSResetType",
]
