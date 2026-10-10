"""
Exceptions - Custom exception classes for QLRisk

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

from typing import Optional, Any, Dict


class CCRException(Exception):
    """
    Base exception for all QLRisk errors.
    All custom exceptions should inherit from this class.
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize CCRException.

        Args:
            message: Error message
            code: Optional error code
            details: Optional additional details
        """
        super().__init__(message)
        self.message = message
        self.code = code or "CCR_ERROR"
        self.details = details or {}

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


class ConfigurationError(CCRException):
    """
    Exception raised for configuration-related errors.
    Examples: missing properties, invalid configuration values.
    """

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ConfigurationError.

        Args:
            message: Error message
            config_key: Configuration key that caused the error
            details: Optional additional details
        """
        if config_key:
            details = details or {}
            details["config_key"] = config_key
        super().__init__(message, code="CONFIG_ERROR", details=details)


class CalculationError(CCRException):
    """
    Exception raised for calculation-related errors.
    Examples: mathematical errors, invalid inputs, convergence failures.
    """

    def __init__(
        self,
        message: str,
        calculator: Optional[str] = None,
        calculation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize CalculationError.

        Args:
            message: Error message
            calculator: Name of the calculator that failed
            calculation_type: Type of calculation that failed
            details: Optional additional details
        """
        details = details or {}
        if calculator:
            details["calculator"] = calculator
        if calculation_type:
            details["calculation_type"] = calculation_type
        super().__init__(message, code="CALC_ERROR", details=details)


class ModelError(CCRException):
    """
    Exception raised for model-related errors.
    Examples: invalid model parameters, model initialization failures.
    """

    def __init__(
        self,
        message: str,
        model_type: Optional[str] = None,
        model_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ModelError.

        Args:
            message: Error message
            model_type: Type of model that caused the error
            model_id: Model identifier
            details: Optional additional details
        """
        details = details or {}
        if model_type:
            details["model_type"] = model_type
        if model_id:
            details["model_id"] = model_id
        super().__init__(message, code="MODEL_ERROR", details=details)


class DataError(CCRException):
    """
    Exception raised for data-related errors.
    Examples: missing data, invalid data format, data validation failures.
    """

    def __init__(
        self,
        message: str,
        data_source: Optional[str] = None,
        data_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize DataError.

        Args:
            message: Error message
            data_source: Source of the data that caused the error
            data_type: Type of data that caused the error
            details: Optional additional details
        """
        details = details or {}
        if data_source:
            details["data_source"] = data_source
        if data_type:
            details["data_type"] = data_type
        super().__init__(message, code="DATA_ERROR", details=details)


class ValidationError(CCRException):
    """
    Exception raised for validation-related errors.
    Examples: invalid input parameters, constraint violations.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        expected: Optional[Any] = None,
        actual: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ValidationError.

        Args:
            message: Error message
            field: Field that failed validation
            expected: Expected value or type
            actual: Actual value received
            details: Optional additional details
        """
        details = details or {}
        if field:
            details["field"] = field
        if expected is not None:
            details["expected"] = str(expected)
        if actual is not None:
            details["actual"] = str(actual)
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class EngineError(CCRException):
    """
    Exception raised for engine-related errors.
    Examples: engine initialization failures, execution errors.
    """

    def __init__(
        self,
        message: str,
        engine_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize EngineError.

        Args:
            message: Error message
            engine_state: Current engine state
            details: Optional additional details
        """
        details = details or {}
        if engine_state:
            details["engine_state"] = engine_state
        super().__init__(message, code="ENGINE_ERROR", details=details)


class QuantLibError(CCRException):
    """
    Exception raised for QuantLib-related errors.
    Examples: QuantLib not installed, QuantLib calculation failures.
    """

    def __init__(
        self,
        message: str,
        quantlib_function: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize QuantLibError.

        Args:
            message: Error message
            quantlib_function: QuantLib function that caused the error
            details: Optional additional details
        """
        details = details or {}
        if quantlib_function:
            details["quantlib_function"] = quantlib_function
        super().__init__(message, code="QUANTLIB_ERROR", details=details)


class CurveError(CCRException):
    """
    Exception raised for curve-related errors.
    Examples: invalid curve data, curve construction failures.
    """

    def __init__(
        self,
        message: str,
        curve_type: Optional[str] = None,
        curve_date: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize CurveError.

        Args:
            message: Error message
            curve_type: Type of curve that caused the error
            curve_date: Curve date if applicable
            details: Optional additional details
        """
        details = details or {}
        if curve_type:
            details["curve_type"] = curve_type
        if curve_date:
            details["curve_date"] = curve_date
        super().__init__(message, code="CURVE_ERROR", details=details)


class TradeError(CCRException):
    """
    Exception raised for trade-related errors.
    Examples: invalid trade data, trade validation failures.
    """

    def __init__(
        self,
        message: str,
        trade_id: Optional[str] = None,
        trade_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize TradeError.

        Args:
            message: Error message
            trade_id: Trade identifier
            trade_type: Type of trade that caused the error
            details: Optional additional details
        """
        details = details or {}
        if trade_id:
            details["trade_id"] = trade_id
        if trade_type:
            details["trade_type"] = trade_type
        super().__init__(message, code="TRADE_ERROR", details=details)
