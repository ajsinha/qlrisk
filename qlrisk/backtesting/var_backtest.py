"""
QLRisk - VaR Backtesting
========================

    result = backtest_var(pnl, var_forecasts, confidence=0.99)
    result.exceptions, result.kupiec_p_value, result.christoffersen_p_value, result.zone

Exception on day t: realised P&L_t < -VaR_t (VaR as a positive loss forecast for day t).

Tests:
  Kupiec POF (unconditional coverage), LR ~ chi2(1)
  Christoffersen independence (Markov), LR ~ chi2(1); conditional coverage LR_POF + LR_IND ~ chi2(2)
  Basel traffic light (99% VaR, 250 days): green 0-4, yellow 5-9, red 10+; plus-factor table

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence

import numpy as np
from scipy.stats import binom, chi2

# Basel plus factor added to the multiplier (3.0) by number of exceptions in 250 days.
BASEL_PLUS_FACTOR = {5: 0.40, 6: 0.50, 7: 0.65, 8: 0.75, 9: 0.85}


def _xlogy(x: float, y: float) -> float:
    return 0.0 if x == 0 else x * np.log(y)


def kupiec_pof(exceptions: int, n: int, confidence: float):
    """Kupiec proportion-of-failures likelihood ratio and p-value."""
    p, x = 1.0 - confidence, exceptions
    phat = x / n
    lr = -2.0 * (_xlogy(n - x, 1 - p) + _xlogy(x, p) - _xlogy(n - x, 1 - phat) - _xlogy(x, phat))
    return float(lr), float(1.0 - chi2.cdf(lr, 1))


def christoffersen_independence(hits: Sequence[bool]):
    """Christoffersen Markov independence likelihood ratio and p-value."""
    h = np.asarray(hits, dtype=int)
    prev, curr = h[:-1], h[1:]
    n00 = int(((prev == 0) & (curr == 0)).sum()); n01 = int(((prev == 0) & (curr == 1)).sum())
    n10 = int(((prev == 1) & (curr == 0)).sum()); n11 = int(((prev == 1) & (curr == 1)).sum())
    pi0 = n01 / (n00 + n01) if n00 + n01 else 0.0
    pi1 = n11 / (n10 + n11) if n10 + n11 else 0.0
    pi = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)
    ll_null = _xlogy(n00 + n10, 1 - pi) + _xlogy(n01 + n11, pi)
    ll_alt = _xlogy(n00, 1 - pi0) + _xlogy(n01, pi0) + _xlogy(n10, 1 - pi1) + _xlogy(n11, pi1)
    lr = max(-2.0 * (ll_null - ll_alt), 0.0)
    return float(lr), float(1.0 - chi2.cdf(lr, 1))


def traffic_light(exceptions: int, n: int = 250, confidence: float = 0.99) -> str:
    """
    Basel traffic-light zone from the cumulative binomial probability of seeing
    at most `exceptions`: green < 95%, yellow < 99.99%, red otherwise
    (for n=250 at 99%: green 0-4, yellow 5-9, red 10+).
    """
    cum = binom.cdf(exceptions, n, 1.0 - confidence)
    if cum < 0.95:
        return "green"
    return "yellow" if cum < 0.9999 else "red"


def basel_multiplier(exceptions: int) -> float:
    """3 + plus factor (Basel 2.5 / MAR99): 3.0 green, 3.4-3.85 yellow, 4.0 red (for 250 days at 99%)."""
    if exceptions <= 4:
        return 3.0
    return 3.0 + BASEL_PLUS_FACTOR.get(exceptions, 1.0)


@dataclass
class VaRBacktestResult:
    """Outcome of a VaR backtest."""
    n: int
    confidence: float
    exceptions: int
    expected_exceptions: float
    exception_labels: List[Any]
    kupiec_lr: float
    kupiec_p_value: float
    independence_lr: float
    independence_p_value: float
    christoffersen_lr: float
    christoffersen_p_value: float
    zone: str
    multiplier: float
    hits: np.ndarray = field(repr=False, default=None)
    
    def passes(self, significance: float = 0.05) -> bool:
        """True if neither coverage nor independence is rejected at `significance`."""
        return self.kupiec_p_value >= significance and self.christoffersen_p_value >= significance
    
    def summary(self) -> str:
        return (f"{self.exceptions} exceptions in {self.n} days (expected {self.expected_exceptions:.1f}); "
                f"Kupiec p={self.kupiec_p_value:.3f}, Christoffersen p={self.christoffersen_p_value:.3f}; "
                f"zone {self.zone}, multiplier {self.multiplier:.2f}")


def backtest_var(
    pnl: Sequence[float],
    var_forecasts: Sequence[float],
    confidence: float = 0.99,
    labels: Optional[Sequence[Any]] = None,
) -> VaRBacktestResult:
    """Run coverage, independence and traffic-light tests on realised P&L vs VaR forecasts."""
    x = np.asarray(pnl, dtype=float)
    v = np.asarray(var_forecasts, dtype=float)
    if x.shape != v.shape or x.ndim != 1 or x.size < 2:
        raise ValueError("pnl and var_forecasts must be 1-D arrays of equal length >= 2")
    labels = list(labels) if labels is not None else list(range(x.size))
    hits = x < -v
    n, k = x.size, int(hits.sum())
    lr_pof, p_pof = kupiec_pof(k, n, confidence)
    lr_ind, p_ind = christoffersen_independence(hits)
    lr_cc = lr_pof + lr_ind
    scaled = int(round(k * 250 / n))                      # zone on a 250-day-equivalent count
    return VaRBacktestResult(
        n=n, confidence=confidence, exceptions=k, expected_exceptions=n * (1 - confidence),
        exception_labels=[labels[i] for i in np.flatnonzero(hits)],
        kupiec_lr=lr_pof, kupiec_p_value=p_pof, independence_lr=lr_ind, independence_p_value=p_ind,
        christoffersen_lr=lr_cc, christoffersen_p_value=float(1.0 - chi2.cdf(lr_cc, 2)),
        zone=traffic_light(k, n, confidence), multiplier=basel_multiplier(scaled), hits=hits,
    )


__all__ = ["backtest_var", "VaRBacktestResult", "kupiec_pof", "christoffersen_independence",
           "traffic_light", "basel_multiplier", "BASEL_PLUS_FACTOR"]
