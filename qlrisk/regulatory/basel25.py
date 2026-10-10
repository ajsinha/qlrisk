"""
QLRisk - Basel 2.5 Market Risk Capital (internal models, pre-FRTB)
=================================================================

    capital = max(VaR_t-1, m * avg60(VaR)) + max(sVaR_t-1, m_s * avg60(sVaR))
    m = m_s = 3 + plus factor from the number of backtesting exceptions (250 days)

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Sequence

import numpy as np

from ..backtesting.var_backtest import basel_multiplier


def basel25_capital(var_series: Sequence[float], svar_series: Sequence[float], exceptions: int = 0) -> dict:
    """VaR / SVaR series are 10-day 99% figures, most recent last (up to 60 are averaged)."""
    var, svar = np.asarray(var_series, float), np.asarray(svar_series, float)
    if var.size == 0 or svar.size == 0:
        raise ValueError("need at least one VaR and one SVaR observation")
    m = basel_multiplier(exceptions)
    var_term = max(var[-1], m * var[-60:].mean())
    svar_term = max(svar[-1], m * svar[-60:].mean())
    return {"capital": float(var_term + svar_term), "var_term": float(var_term), "svar_term": float(svar_term),
            "multiplier": m}


__all__ = ["basel25_capital"]
