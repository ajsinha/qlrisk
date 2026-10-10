"""
QLRisk - Core Module v1.3.0
==========================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.

---

Common utilities and configurations for QLRisk.

Modules:
- properties_configurator: Thread-safe configuration management with auto-reload
- logger: Customizable logging with rotation and formatting
- timer: Performance timing utilities and decorators
- thread_pool: Managed thread pool for parallel execution
- exceptions: Custom exception hierarchy (CCRException and subclasses)
- validators: Input validation utilities
- date_utils: Business day and date calculations
- numeric_utils: Numerical computation helpers (interpolation, statistics)
"""

__version__ = "1.3.0"

from .properties_configurator import PropertiesConfigurator
from .logger import Logger, get_logger
from .timer import Timer, timed
from .thread_pool import ThreadPoolManager
from .exceptions import (
    CCRException,
    ConfigurationError,
    CalculationError,
    ModelError,
    DataError,
    ValidationError,
    CurveError
)
from .validators import Validators
from .date_utils import DateUtils
from .numeric_utils import NumericUtils

__all__ = [
    "__version__",
    "PropertiesConfigurator",
    "Logger",
    "get_logger",
    "Timer",
    "timed",
    "ThreadPoolManager",
    "CCRException",
    "ConfigurationError",
    "CalculationError",
    "ModelError",
    "DataError",
    "ValidationError",
    "CurveError",
    "Validators",
    "DateUtils",
    "NumericUtils",
]
