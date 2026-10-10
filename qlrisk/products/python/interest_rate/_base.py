"""
Common imports and utilities for Interest Rate products.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq

from ...base import (
    BaseProduct, ProductType, AssetClass, Currency, FloatingRateIndex,
    DayCountConvention, PaymentFrequency, BusinessDayConvention,
    OptionType, OptionStyle, SettlementType,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction, discount_factor, forward_rate,
    bachelier_call, bachelier_put
)

# Copyright notice
COPYRIGHT = """
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""


@dataclass
class IRSLeg:
    """Specification of a single swap leg."""
    is_fixed: bool
    rate: Optional[float] = None
    index: Optional[FloatingRateIndex] = None
    frequency: PaymentFrequency = PaymentFrequency.QUARTERLY
    day_count: DayCountConvention = DayCountConvention.ACT_360
    notional: float = 0.0
    currency: Currency = Currency.USD
