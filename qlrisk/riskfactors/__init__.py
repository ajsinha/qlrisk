"""
QLRisk - Risk Factors Module v2.2.1
===================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.

---

The risk-factor layer shared by market risk and CCR: names every market
input, reads and writes it in products.base.MarketData, shocks market data
copy-on-write, and stores factor histories.

Quick Start:
-----------
    from qlrisk.riskfactors import enumerate_risk_factors, apply_shocks, ShockType

    for key in enumerate_risk_factors(md):
        print(key, key.risk_class.value)            # IR.FWD.SOFR.5Y IR, FX.EURUSD FX, ...

    shocked = apply_shocks(md, {"FX.EURUSD": 0.01}, ShockType.RELATIVE)
"""

from .taxonomy import (
    RiskClass, FactorKind, FieldSpec, FIELD_SPECS, RiskFactorKey, RiskFactorLike,
    as_key, format_tenor, parse_tenor, infer_vol_risk_class,
)
from .mapping import (
    enumerate_risk_factors, get_factor_value, set_factor_value,
    clone_market_data, detect_risk_factors,
)
from .shocks import (
    ShockType, Shock, shocked_value, apply_shocks, set_factors,
    CurveShape, parallel, twist, butterfly, curve_shocks,
)
from .timeseries import RiskFactorTimeSeries, DEFAULT_RETURN_TYPES

__all__ = [
    # taxonomy
    "RiskClass", "FactorKind", "FieldSpec", "FIELD_SPECS", "RiskFactorKey", "RiskFactorLike",
    "as_key", "format_tenor", "parse_tenor", "infer_vol_risk_class",
    # mapping
    "enumerate_risk_factors", "get_factor_value", "set_factor_value",
    "clone_market_data", "detect_risk_factors",
    # shocks
    "ShockType", "Shock", "shocked_value", "apply_shocks", "set_factors",
    "CurveShape", "parallel", "twist", "butterfly", "curve_shocks",
    # time series
    "RiskFactorTimeSeries", "DEFAULT_RETURN_TYPES",
]
