"""
QLRisk - QuantLib Products v1.2.0
================================================

QuantLib-based implementations for high-performance pricing.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False

from .interest_rate import (
    InterestRateSwapQL, SwaptionQL, InterestRateCapQL, InterestRateFloorQL,
    to_ql_date, from_ql_date, build_yield_curve,
)
from .fx import FXForwardQL, FXOptionQL
from .fixed_income import FixedRateBondQL, FloatingRateBondQL, ZeroCouponBondQL

__all__ = [
    "QUANTLIB_AVAILABLE",
    "InterestRateSwapQL", "SwaptionQL", "InterestRateCapQL", "InterestRateFloorQL",
    "FXForwardQL", "FXOptionQL",
    "FixedRateBondQL", "FloatingRateBondQL", "ZeroCouponBondQL",
    "to_ql_date", "from_ql_date", "build_yield_curve",
]
