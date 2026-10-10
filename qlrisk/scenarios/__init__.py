"""
QLRisk - Scenarios Module v1.3.0
================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.

---

Market scenarios for VaR / ES / stress testing: historical, age-weighted,
filtered historical, Monte Carlo and hypothetical (from shocks), plus
stressed-period search.
"""

from .scenario_set import ScenarioSet
from .generators import (
    historical_scenarios, filtered_historical_scenarios, monte_carlo_scenarios,
    age_weights, ewma_volatility, covariance,
)
from .stressed_period import StressWindow, find_stress_window

__all__ = [
    "ScenarioSet", "historical_scenarios", "filtered_historical_scenarios", "monte_carlo_scenarios",
    "age_weights", "ewma_volatility", "covariance", "StressWindow", "find_stress_window",
]
