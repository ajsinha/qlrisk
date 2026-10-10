"""
QLRisk - SA-CCR (re-export)
===========================

The SA-CCR calculator lives in qlrisk.calculator.python.saccr_calculator; it is
re-exported here so all regulatory capital is reachable from qlrisk.regulatory.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from ..calculator.python.saccr_calculator import *  # noqa: F401,F403
from ..calculator.python import saccr_calculator as _saccr

__all__ = getattr(_saccr, "__all__", [n for n in dir(_saccr) if not n.startswith("_")])
