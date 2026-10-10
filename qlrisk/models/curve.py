"""
Curve Models - Yield curves, credit curves, and volatility surfaces

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import math

from .base import ModelBase
# from ..core.exceptions import CurveError  # Removed - self-contained
# from ..core.numeric_utils import NumericUtils  # Removed - self-contained


class CurveType(Enum):
    """Curve type enumeration."""
    YIELD = "yield"
    DISCOUNT = "discount"
    ZERO = "zero"
    FORWARD = "forward"
    CREDIT = "credit"
    HAZARD = "hazard"
    VOLATILITY = "volatility"


class InterpolationMethod(Enum):
    """Interpolation method enumeration."""
    LINEAR = "linear"
    LOG_LINEAR = "log_linear"
    CUBIC_SPLINE = "cubic_spline"
    FLAT = "flat"


@dataclass
class Curve(ModelBase):
    """
    Base curve class for all curve types.
    """
    curve_id: str = ""
    curve_type: CurveType = CurveType.YIELD
    currency: str = "USD"
    curve_date: date = field(default_factory=date.today)
    
    # Curve data: list of (time, value) tuples
    tenors: List[float] = field(default_factory=list)  # Time in years
    values: List[float] = field(default_factory=list)  # Rate or DF values
    
    interpolation: InterpolationMethod = InterpolationMethod.LOG_LINEAR
    
    def validate(self) -> bool:
        """Validate curve data."""
        if len(self.tenors) != len(self.values):
            raise ValueError(
                "Tenors and values must have same length",
                curve_type=self.curve_type.value
            )
        
        # Check tenors are sorted
        for i in range(1, len(self.tenors)):
            if self.tenors[i] <= self.tenors[i-1]:
                raise ValueError(
                    "Tenors must be strictly increasing",
                    curve_type=self.curve_type.value
                )
        
        return True

    def get_value(self, tenor: float) -> float:
        """
        Get interpolated value at tenor.

        Args:
            tenor: Time in years

        Returns:
            Interpolated value
        """
        if not self.tenors:
            raise ValueError("Curve has no data")
        
        if self.interpolation == InterpolationMethod.LINEAR:
            return NumericUtils.interpolate_linear(tenor, self.tenors, self.values)
        elif self.interpolation == InterpolationMethod.LOG_LINEAR:
            return NumericUtils.interpolate_log_linear(tenor, self.tenors, self.values)
        elif self.interpolation == InterpolationMethod.FLAT:
            # Return nearest value
            if tenor <= self.tenors[0]:
                return self.values[0]
            if tenor >= self.tenors[-1]:
                return self.values[-1]
            for i, t in enumerate(self.tenors):
                if t >= tenor:
                    return self.values[i]
            return self.values[-1]
        else:
            return NumericUtils.interpolate_linear(tenor, self.tenors, self.values)

    def add_point(self, tenor: float, value: float):
        """Add a point to the curve."""
        # Insert in sorted order
        for i, t in enumerate(self.tenors):
            if tenor < t:
                self.tenors.insert(i, tenor)
                self.values.insert(i, value)
                return
            elif tenor == t:
                self.values[i] = value
                return
        
        self.tenors.append(tenor)
        self.values.append(value)

    def shift(self, amount: float) -> 'Curve':
        """
        Create parallel shifted curve.

        Args:
            amount: Shift amount (in same units as values)

        Returns:
            Shifted curve
        """
        new_curve = self.clone()
        new_curve.values = [v + amount for v in self.values]
        return new_curve


@dataclass
class YieldCurve(Curve):
    """
    Yield curve for interest rate discounting.
    """
    curve_type: CurveType = CurveType.YIELD
    
    def validate(self) -> bool:
        """Validate yield curve."""
        super().validate()
        return True

    def discount_factor(self, tenor: float) -> float:
        """
        Get discount factor at tenor.

        Args:
            tenor: Time in years

        Returns:
            Discount factor
        """
        if self.curve_type == CurveType.DISCOUNT:
            return self.get_value(tenor)
        else:
            # Convert zero rate to discount factor
            rate = self.get_value(tenor)
            return math.exp(-rate * tenor)

    def zero_rate(self, tenor: float) -> float:
        """
        Get zero rate at tenor.

        Args:
            tenor: Time in years

        Returns:
            Zero rate (continuous compounding)
        """
        if self.curve_type == CurveType.ZERO:
            return self.get_value(tenor)
        else:
            df = self.discount_factor(tenor)
            if tenor > 0:
                return -math.log(df) / tenor
            return 0.0

    def forward_rate(self, start_tenor: float, end_tenor: float) -> float:
        """
        Get forward rate between two tenors.

        Args:
            start_tenor: Start time in years
            end_tenor: End time in years

        Returns:
            Forward rate
        """
        if end_tenor <= start_tenor:
            raise ValueError("End tenor must be greater than start tenor")
        
        df_start = self.discount_factor(start_tenor)
        df_end = self.discount_factor(end_tenor)
        
        return (df_start / df_end - 1) / (end_tenor - start_tenor)

    def instantaneous_forward(self, tenor: float, delta: float = 0.001) -> float:
        """
        Get instantaneous forward rate.

        Args:
            tenor: Time in years
            delta: Small time increment

        Returns:
            Instantaneous forward rate
        """
        return self.forward_rate(tenor, tenor + delta)


@dataclass
class CreditCurve(Curve):
    """
    Credit curve for default probability and survival probability.
    """
    curve_type: CurveType = CurveType.HAZARD
    recovery_rate: float = 0.4
    
    def validate(self) -> bool:
        """Validate credit curve."""
        super().validate()
        
        if not 0 <= self.recovery_rate <= 1:
            raise ValueError(
                "Recovery rate must be between 0 and 1",
                curve_type=self.curve_type.value
            )
        
        return True

    def hazard_rate(self, tenor: float) -> float:
        """
        Get hazard rate at tenor.

        Args:
            tenor: Time in years

        Returns:
            Hazard rate
        """
        return self.get_value(tenor)

    def survival_probability(self, tenor: float) -> float:
        """
        Get survival probability at tenor.

        Args:
            tenor: Time in years

        Returns:
            Survival probability
        """
        # Integrate hazard rate (simplified: assume constant hazard)
        h = self.hazard_rate(tenor)
        return math.exp(-h * tenor)

    def default_probability(self, tenor: float) -> float:
        """
        Get cumulative default probability at tenor.

        Args:
            tenor: Time in years

        Returns:
            Default probability
        """
        return 1 - self.survival_probability(tenor)

    def marginal_default_probability(
        self,
        start_tenor: float,
        end_tenor: float
    ) -> float:
        """
        Get marginal default probability between two tenors.

        Args:
            start_tenor: Start time in years
            end_tenor: End time in years

        Returns:
            Marginal default probability
        """
        sp_start = self.survival_probability(start_tenor)
        sp_end = self.survival_probability(end_tenor)
        return sp_start - sp_end

    def expected_loss(self, tenor: float, exposure: float) -> float:
        """
        Calculate expected loss at tenor.

        Args:
            tenor: Time in years
            exposure: Exposure amount

        Returns:
            Expected loss
        """
        pd = self.default_probability(tenor)
        lgd = 1 - self.recovery_rate
        return pd * lgd * exposure


@dataclass
class VolatilitySurface(ModelBase):
    """
    Volatility surface for option pricing.
    """
    surface_id: str = ""
    underlying: str = ""
    currency: str = "USD"
    surface_date: date = field(default_factory=date.today)
    
    # Surface data: (expiry, strike) -> volatility
    expiries: List[float] = field(default_factory=list)  # Time in years
    strikes: List[float] = field(default_factory=list)  # Strike values
    volatilities: List[List[float]] = field(default_factory=list)  # 2D matrix
    
    # ATM volatility term structure
    atm_tenors: List[float] = field(default_factory=list)
    atm_vols: List[float] = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate volatility surface."""
        if self.volatilities:
            if len(self.volatilities) != len(self.expiries):
                raise ValueError("Volatilities rows must match expiries")
            for row in self.volatilities:
                if len(row) != len(self.strikes):
                    raise ValueError("Volatilities columns must match strikes")
        return True

    def get_volatility(
        self,
        expiry: float,
        strike: Optional[float] = None
    ) -> float:
        """
        Get volatility at expiry and strike.

        Args:
            expiry: Time to expiry in years
            strike: Strike price (None for ATM)

        Returns:
            Implied volatility
        """
        if strike is None:
            # Return ATM volatility
            if self.atm_tenors and self.atm_vols:
                return NumericUtils.interpolate_linear(
                    expiry, self.atm_tenors, self.atm_vols
                )
            elif self.volatilities:
                # Use middle strike as ATM proxy
                mid_idx = len(self.strikes) // 2
                vols_at_mid = [row[mid_idx] for row in self.volatilities]
                return NumericUtils.interpolate_linear(expiry, self.expiries, vols_at_mid)
            else:
                raise ValueError("No volatility data available")
        
        # Full surface interpolation
        if not self.volatilities:
            raise ValueError("No volatility surface data")
        
        # Bilinear interpolation
        # Find expiry interval
        exp_idx = 0
        for i, e in enumerate(self.expiries):
            if e >= expiry:
                exp_idx = i
                break
        else:
            exp_idx = len(self.expiries) - 1
        
        # Find strike interval
        strike_idx = 0
        for i, s in enumerate(self.strikes):
            if s >= strike:
                strike_idx = i
                break
        else:
            strike_idx = len(self.strikes) - 1
        
        # Get volatility at nearest point
        return self.volatilities[exp_idx][strike_idx]

    def term_atm_vol(self, expiry: float) -> float:
        """Get ATM term volatility."""
        return self.get_volatility(expiry, None)
