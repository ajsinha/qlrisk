"""
Numeric Utilities - Numerical computation utilities for QLRisk

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

import math
from typing import List, Optional, Tuple, Union
from decimal import Decimal, ROUND_HALF_UP
import statistics


class NumericUtils:
    """
    Utility class for common numerical operations.
    Provides static methods for financial calculations and statistics.
    """

    # Constants
    EPSILON = 1e-10
    SQRT_2PI = math.sqrt(2 * math.pi)
    SQRT_2 = math.sqrt(2)

    @staticmethod
    def round_decimal(
        value: Union[float, Decimal],
        decimal_places: int = 2
    ) -> Decimal:
        """
        Round to specified decimal places.

        Args:
            value: Value to round
            decimal_places: Number of decimal places

        Returns:
            Rounded Decimal value
        """
        if isinstance(value, float):
            value = Decimal(str(value))
        
        quantize_str = Decimal("0." + "0" * decimal_places)
        return value.quantize(quantize_str, rounding=ROUND_HALF_UP)

    @staticmethod
    def is_close(
        a: float,
        b: float,
        rel_tol: float = 1e-9,
        abs_tol: float = 0.0
    ) -> bool:
        """
        Check if two floats are close.

        Args:
            a: First value
            b: Second value
            rel_tol: Relative tolerance
            abs_tol: Absolute tolerance

        Returns:
            True if values are close
        """
        return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)

    @staticmethod
    def norm_cdf(x: float) -> float:
        """
        Standard normal cumulative distribution function.

        Args:
            x: Input value

        Returns:
            Cumulative probability
        """
        return 0.5 * (1 + math.erf(x / NumericUtils.SQRT_2))

    @staticmethod
    def norm_pdf(x: float) -> float:
        """
        Standard normal probability density function.

        Args:
            x: Input value

        Returns:
            Probability density
        """
        return math.exp(-0.5 * x * x) / NumericUtils.SQRT_2PI

    @staticmethod
    def norm_inv(p: float) -> float:
        """
        Inverse of standard normal CDF (quantile function).
        Uses Abramowitz and Stegun approximation.

        Args:
            p: Probability (0 < p < 1)

        Returns:
            Quantile value
        """
        if p <= 0 or p >= 1:
            raise ValueError("Probability must be between 0 and 1")
        
        # Rational approximation for lower region
        a = [
            -3.969683028665376e+01,
            2.209460984245205e+02,
            -2.759285104469687e+02,
            1.383577518672690e+02,
            -3.066479806614716e+01,
            2.506628277459239e+00
        ]
        
        b = [
            -5.447609879822406e+01,
            1.615858368580409e+02,
            -1.556989798598866e+02,
            6.680131188771972e+01,
            -1.328068155288572e+01
        ]
        
        c = [
            -7.784894002430293e-03,
            -3.223964580411365e-01,
            -2.400758277161838e+00,
            -2.549732539343734e+00,
            4.374664141464968e+00,
            2.938163982698783e+00
        ]
        
        d = [
            7.784695709041462e-03,
            3.224671290700398e-01,
            2.445134137142996e+00,
            3.754408661907416e+00
        ]
        
        p_low = 0.02425
        p_high = 1 - p_low
        
        if p < p_low:
            q = math.sqrt(-2 * math.log(p))
            return (((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
                   ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1)
        elif p <= p_high:
            q = p - 0.5
            r = q * q
            return (((((a[0]*r + a[1])*r + a[2])*r + a[3])*r + a[4])*r + a[5])*q / \
                   (((((b[0]*r + b[1])*r + b[2])*r + b[3])*r + b[4])*r + 1)
        else:
            q = math.sqrt(-2 * math.log(1 - p))
            return -(((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
                    ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1)

    @staticmethod
    def interpolate_linear(
        x: float,
        x_values: List[float],
        y_values: List[float]
    ) -> float:
        """
        Linear interpolation.

        Args:
            x: Value to interpolate at
            x_values: X coordinates (must be sorted ascending)
            y_values: Y coordinates

        Returns:
            Interpolated y value
        """
        if len(x_values) != len(y_values):
            raise ValueError("x_values and y_values must have same length")
        
        if len(x_values) < 2:
            raise ValueError("Need at least 2 points for interpolation")
        
        # Handle extrapolation
        if x <= x_values[0]:
            return y_values[0]
        if x >= x_values[-1]:
            return y_values[-1]
        
        # Find interval
        for i in range(len(x_values) - 1):
            if x_values[i] <= x <= x_values[i + 1]:
                t = (x - x_values[i]) / (x_values[i + 1] - x_values[i])
                return y_values[i] + t * (y_values[i + 1] - y_values[i])
        
        return y_values[-1]

    @staticmethod
    def interpolate_log_linear(
        x: float,
        x_values: List[float],
        y_values: List[float]
    ) -> float:
        """
        Log-linear interpolation (interpolate on log of y values).

        Args:
            x: Value to interpolate at
            x_values: X coordinates (must be sorted ascending)
            y_values: Y coordinates (must be positive)

        Returns:
            Interpolated y value
        """
        log_y = [math.log(y) for y in y_values]
        log_result = NumericUtils.interpolate_linear(x, x_values, log_y)
        return math.exp(log_result)

    @staticmethod
    def percentile(values: List[float], p: float) -> float:
        """
        Calculate percentile of a list of values.

        Args:
            values: List of values
            p: Percentile (0-100)

        Returns:
            Percentile value
        """
        if not values:
            raise ValueError("Cannot compute percentile of empty list")
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        k = (n - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        
        if f == c:
            return sorted_values[int(k)]
        
        d0 = sorted_values[int(f)] * (c - k)
        d1 = sorted_values[int(c)] * (k - f)
        
        return d0 + d1

    @staticmethod
    def var(
        values: List[float],
        confidence_level: float = 0.99
    ) -> float:
        """
        Calculate Value at Risk (VaR).

        Args:
            values: List of P&L or return values
            confidence_level: Confidence level (e.g., 0.99)

        Returns:
            VaR value (positive number representing potential loss)
        """
        percentile_level = (1 - confidence_level) * 100
        return -NumericUtils.percentile(values, percentile_level)

    @staticmethod
    def expected_shortfall(
        values: List[float],
        confidence_level: float = 0.99
    ) -> float:
        """
        Calculate Expected Shortfall (CVaR).

        Args:
            values: List of P&L or return values
            confidence_level: Confidence level (e.g., 0.99)

        Returns:
            ES value (positive number representing average loss beyond VaR)
        """
        sorted_values = sorted(values)
        cutoff_index = int(len(sorted_values) * (1 - confidence_level))
        
        if cutoff_index == 0:
            return -sorted_values[0]
        
        tail_values = sorted_values[:cutoff_index]
        return -statistics.mean(tail_values)

    @staticmethod
    def discount_factor(
        rate: float,
        time: float,
        compounding: str = "continuous"
    ) -> float:
        """
        Calculate discount factor.

        Args:
            rate: Interest rate
            time: Time in years
            compounding: "continuous", "annual", "semiannual", "quarterly", "monthly"

        Returns:
            Discount factor
        """
        if compounding == "continuous":
            return math.exp(-rate * time)
        elif compounding == "annual":
            return 1 / (1 + rate) ** time
        elif compounding == "semiannual":
            return 1 / (1 + rate / 2) ** (2 * time)
        elif compounding == "quarterly":
            return 1 / (1 + rate / 4) ** (4 * time)
        elif compounding == "monthly":
            return 1 / (1 + rate / 12) ** (12 * time)
        else:
            raise ValueError(f"Unknown compounding: {compounding}")

    @staticmethod
    def forward_rate(
        rate1: float,
        time1: float,
        rate2: float,
        time2: float
    ) -> float:
        """
        Calculate forward rate from spot rates.

        Args:
            rate1: Short rate
            time1: Short time
            rate2: Long rate
            time2: Long time

        Returns:
            Forward rate
        """
        if time2 <= time1:
            raise ValueError("time2 must be greater than time1")
        
        df1 = math.exp(-rate1 * time1)
        df2 = math.exp(-rate2 * time2)
        
        return -math.log(df2 / df1) / (time2 - time1)

    @staticmethod
    def black_scholes_d1(
        S: float,
        K: float,
        r: float,
        sigma: float,
        T: float
    ) -> float:
        """
        Calculate Black-Scholes d1 parameter.

        Args:
            S: Spot price
            K: Strike price
            r: Risk-free rate
            sigma: Volatility
            T: Time to maturity

        Returns:
            d1 value
        """
        if T <= 0 or sigma <= 0:
            raise ValueError("T and sigma must be positive")
        
        return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

    @staticmethod
    def black_scholes_d2(
        S: float,
        K: float,
        r: float,
        sigma: float,
        T: float
    ) -> float:
        """
        Calculate Black-Scholes d2 parameter.

        Args:
            S: Spot price
            K: Strike price
            r: Risk-free rate
            sigma: Volatility
            T: Time to maturity

        Returns:
            d2 value
        """
        d1 = NumericUtils.black_scholes_d1(S, K, r, sigma, T)
        return d1 - sigma * math.sqrt(T)

    @staticmethod
    def newton_raphson(
        func,
        derivative,
        x0: float,
        tolerance: float = 1e-8,
        max_iterations: int = 100
    ) -> Tuple[float, bool]:
        """
        Newton-Raphson root finding.

        Args:
            func: Function to find root of
            derivative: Derivative of function
            x0: Initial guess
            tolerance: Convergence tolerance
            max_iterations: Maximum iterations

        Returns:
            Tuple of (root, converged)
        """
        x = x0
        
        for _ in range(max_iterations):
            fx = func(x)
            dfx = derivative(x)
            
            if abs(dfx) < NumericUtils.EPSILON:
                return x, False
            
            x_new = x - fx / dfx
            
            if abs(x_new - x) < tolerance:
                return x_new, True
            
            x = x_new
        
        return x, False

    @staticmethod
    def bisection(
        func,
        a: float,
        b: float,
        tolerance: float = 1e-8,
        max_iterations: int = 100
    ) -> Tuple[float, bool]:
        """
        Bisection root finding.

        Args:
            func: Function to find root of
            a: Left bound
            b: Right bound
            tolerance: Convergence tolerance
            max_iterations: Maximum iterations

        Returns:
            Tuple of (root, converged)
        """
        fa = func(a)
        fb = func(b)
        
        if fa * fb > 0:
            raise ValueError("Function must have opposite signs at bounds")
        
        for _ in range(max_iterations):
            c = (a + b) / 2
            fc = func(c)
            
            if abs(fc) < tolerance or (b - a) / 2 < tolerance:
                return c, True
            
            if fa * fc < 0:
                b = c
                fb = fc
            else:
                a = c
                fa = fc
        
        return (a + b) / 2, False

    @staticmethod
    def present_value(
        cash_flows: List[float],
        times: List[float],
        rate: float
    ) -> float:
        """
        Calculate present value of cash flows.

        Args:
            cash_flows: List of cash flow amounts
            times: List of times (in years) for each cash flow
            rate: Discount rate

        Returns:
            Present value
        """
        if len(cash_flows) != len(times):
            raise ValueError("cash_flows and times must have same length")
        
        pv = 0.0
        for cf, t in zip(cash_flows, times):
            pv += cf * math.exp(-rate * t)
        
        return pv

    @staticmethod
    def irr(
        cash_flows: List[float],
        times: List[float],
        initial_guess: float = 0.1,
        tolerance: float = 1e-8
    ) -> Tuple[float, bool]:
        """
        Calculate Internal Rate of Return.

        Args:
            cash_flows: List of cash flow amounts
            times: List of times for each cash flow
            initial_guess: Initial rate guess
            tolerance: Convergence tolerance

        Returns:
            Tuple of (IRR, converged)
        """
        def npv(rate):
            return NumericUtils.present_value(cash_flows, times, rate)
        
        def npv_derivative(rate):
            return sum(-t * cf * math.exp(-rate * t) for cf, t in zip(cash_flows, times))
        
        return NumericUtils.newton_raphson(npv, npv_derivative, initial_guess, tolerance)
