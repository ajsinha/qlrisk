"""
QLRisk - Sensitivities Module v2.1.0
====================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.

---

Bump-and-reprice sensitivities for every product: DV01, CS01, delta,
gamma, vega, cross-gamma, theta, with tenor ladders and FRTB vertices.

Quick Start:
-----------
    from qlrisk.sensitivities import SensitivityEngine, FRTB_GIRR_VERTICES

    result = SensitivityEngine().compute(trades, market_data, reporting_currency="USD")
    print(result.aggregate(("risk_class", "measure")))
    print(result.ladder("forward_curves", "SOFR", vertices=FRTB_GIRR_VERTICES))
"""

from .measures import SensitivityMeasure, BumpSpec, DEFAULT_BUMPS, measure_for, Sensitivity
from .ladders import (
    STANDARD_TENORS, FRTB_GIRR_VERTICES, FRTB_CSR_VERTICES, FRTB_VEGA_MATURITIES,
    rebucket, TenorLadder, build_ladders,
)
from .results import SensitivityResult, SensitivityError
from .engine import SensitivityEngine, compute_sensitivities, fx_convert, fx_pairs_used, CENTRAL, FORWARD

__all__ = [
    "SensitivityMeasure", "BumpSpec", "DEFAULT_BUMPS", "measure_for", "Sensitivity",
    "STANDARD_TENORS", "FRTB_GIRR_VERTICES", "FRTB_CSR_VERTICES", "FRTB_VEGA_MATURITIES",
    "rebucket", "TenorLadder", "build_ladders",
    "SensitivityResult", "SensitivityError",
    "SensitivityEngine", "compute_sensitivities", "fx_convert", "fx_pairs_used", "CENTRAL", "FORWARD",
]
