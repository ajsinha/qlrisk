"""
QLRisk - Stressed Period Search
===============================

Find the window of history that maximises VaR (or ES) of the current
portfolio, as used for Stressed VaR and FRTB stress calibration.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass
from typing import Any, List, Sequence

import numpy as np

from ..calculator.python.var_calculators import expected_shortfall, value_at_risk


@dataclass
class StressWindow:
    """Result of a stressed-period search."""
    start: Any
    end: Any
    start_index: int
    end_index: int            # exclusive
    value: float              # VaR/ES of the window
    measure: str
    profile: List[float]      # VaR/ES of every candidate window, in order


def find_stress_window(
    pnl: Sequence[float],
    labels: Sequence[Any],
    window: int = 250,
    confidence: float = 0.99,
    measure: str = "var",
    step: int = 1,
) -> StressWindow:
    """
    Slide a `window`-scenario window over a chronological P&L vector and return the
    window with the largest VaR (measure='var') or ES (measure='es').
    """
    x = np.asarray(pnl, dtype=float)
    if len(x) < window:
        raise ValueError(f"need at least {window} scenarios, got {len(x)}")
    fn = value_at_risk if measure == "var" else expected_shortfall
    starts = list(range(0, len(x) - window + 1, step))
    profile = [fn(x[s:s + window], confidence) for s in starts]
    best = int(np.argmax(profile))
    s = starts[best]
    return StressWindow(labels[s], labels[s + window - 1], s, s + window, profile[best], measure, profile)


__all__ = ["StressWindow", "find_stress_window"]
