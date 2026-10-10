"""
Validators - Input validation utilities for QLRisk

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

from typing import Any, Optional, List, Type, Union, Callable
from datetime import datetime, date
from decimal import Decimal
import re

from .exceptions import ValidationError


class Validators:
    """
    Utility class for common validation operations.
    Provides static methods for validating various data types and constraints.
    """

    @staticmethod
    def not_none(value: Any, field_name: str) -> Any:
        """
        Validate that value is not None.

        Args:
            value: Value to validate
            field_name: Name of the field for error message

        Returns:
            The value if valid

        Raises:
            ValidationError: If value is None
        """
        if value is None:
            raise ValidationError(
                f"{field_name} cannot be None",
                field=field_name,
                expected="non-null value",
                actual=None
            )
        return value

    @staticmethod
    def not_empty(value: Union[str, list, dict], field_name: str) -> Any:
        """
        Validate that value is not empty.

        Args:
            value: Value to validate (string, list, or dict)
            field_name: Name of the field for error message

        Returns:
            The value if valid

        Raises:
            ValidationError: If value is empty
        """
        if not value:
            raise ValidationError(
                f"{field_name} cannot be empty",
                field=field_name,
                expected="non-empty value",
                actual=value
            )
        return value

    @staticmethod
    def positive(value: Union[int, float, Decimal], field_name: str) -> Union[int, float, Decimal]:
        """
        Validate that numeric value is positive.

        Args:
            value: Numeric value to validate
            field_name: Name of the field for error message

        Returns:
            The value if valid

        Raises:
            ValidationError: If value is not positive
        """
        if value <= 0:
            raise ValidationError(
                f"{field_name} must be positive",
                field=field_name,
                expected="> 0",
                actual=value
            )
        return value

    @staticmethod
    def non_negative(value: Union[int, float, Decimal], field_name: str) -> Union[int, float, Decimal]:
        """
        Validate that numeric value is non-negative.

        Args:
            value: Numeric value to validate
            field_name: Name of the field for error message

        Returns:
            The value if valid

        Raises:
            ValidationError: If value is negative
        """
        if value < 0:
            raise ValidationError(
                f"{field_name} must be non-negative",
                field=field_name,
                expected=">= 0",
                actual=value
            )
        return value

    @staticmethod
    def in_range(
        value: Union[int, float, Decimal],
        field_name: str,
        min_val: Optional[Union[int, float, Decimal]] = None,
        max_val: Optional[Union[int, float, Decimal]] = None,
        inclusive: bool = True
    ) -> Union[int, float, Decimal]:
        """
        Validate that value is within range.

        Args:
            value: Numeric value to validate
            field_name: Name of the field for error message
            min_val: Minimum value (optional)
            max_val: Maximum value (optional)
            inclusive: Whether bounds are inclusive

        Returns:
            The value if valid

        Raises:
            ValidationError: If value is out of range
        """
        if inclusive:
            if min_val is not None and value < min_val:
                raise ValidationError(
                    f"{field_name} must be >= {min_val}",
                    field=field_name,
                    expected=f">= {min_val}",
                    actual=value
                )
            if max_val is not None and value > max_val:
                raise ValidationError(
                    f"{field_name} must be <= {max_val}",
                    field=field_name,
                    expected=f"<= {max_val}",
                    actual=value
                )
        else:
            if min_val is not None and value <= min_val:
                raise ValidationError(
                    f"{field_name} must be > {min_val}",
                    field=field_name,
                    expected=f"> {min_val}",
                    actual=value
                )
            if max_val is not None and value >= max_val:
                raise ValidationError(
                    f"{field_name} must be < {max_val}",
                    field=field_name,
                    expected=f"< {max_val}",
                    actual=value
                )
        return value

    @staticmethod
    def probability(value: Union[float, Decimal], field_name: str) -> Union[float, Decimal]:
        """
        Validate that value is a valid probability (0 to 1).

        Args:
            value: Value to validate
            field_name: Name of the field for error message

        Returns:
            The value if valid

        Raises:
            ValidationError: If value is not a valid probability
        """
        return Validators.in_range(value, field_name, min_val=0, max_val=1)

    @staticmethod
    def percentage(value: Union[float, Decimal], field_name: str) -> Union[float, Decimal]:
        """
        Validate that value is a valid percentage (0 to 100).

        Args:
            value: Value to validate
            field_name: Name of the field for error message

        Returns:
            The value if valid

        Raises:
            ValidationError: If value is not a valid percentage
        """
        return Validators.in_range(value, field_name, min_val=0, max_val=100)

    @staticmethod
    def is_type(value: Any, expected_type: Type, field_name: str) -> Any:
        """
        Validate that value is of expected type.

        Args:
            value: Value to validate
            expected_type: Expected type
            field_name: Name of the field for error message

        Returns:
            The value if valid

        Raises:
            ValidationError: If value is not of expected type
        """
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"{field_name} must be of type {expected_type.__name__}",
                field=field_name,
                expected=expected_type.__name__,
                actual=type(value).__name__
            )
        return value

    @staticmethod
    def in_list(value: Any, valid_values: List[Any], field_name: str) -> Any:
        """
        Validate that value is in a list of valid values.

        Args:
            value: Value to validate
            valid_values: List of valid values
            field_name: Name of the field for error message

        Returns:
            The value if valid

        Raises:
            ValidationError: If value is not in the list
        """
        if value not in valid_values:
            raise ValidationError(
                f"{field_name} must be one of {valid_values}",
                field=field_name,
                expected=f"one of {valid_values}",
                actual=value
            )
        return value

    @staticmethod
    def matches_pattern(value: str, pattern: str, field_name: str) -> str:
        """
        Validate that string matches a regex pattern.

        Args:
            value: String value to validate
            pattern: Regex pattern
            field_name: Name of the field for error message

        Returns:
            The value if valid

        Raises:
            ValidationError: If value doesn't match pattern
        """
        if not re.match(pattern, value):
            raise ValidationError(
                f"{field_name} must match pattern {pattern}",
                field=field_name,
                expected=f"matching {pattern}",
                actual=value
            )
        return value

    @staticmethod
    def date_not_in_future(value: Union[datetime, date], field_name: str) -> Union[datetime, date]:
        """
        Validate that date is not in the future.

        Args:
            value: Date value to validate
            field_name: Name of the field for error message

        Returns:
            The value if valid

        Raises:
            ValidationError: If date is in the future
        """
        today = date.today()
        check_date = value.date() if isinstance(value, datetime) else value
        
        if check_date > today:
            raise ValidationError(
                f"{field_name} cannot be in the future",
                field=field_name,
                expected=f"<= {today}",
                actual=check_date
            )
        return value

    @staticmethod
    def date_after(
        value: Union[datetime, date],
        after_date: Union[datetime, date],
        field_name: str
    ) -> Union[datetime, date]:
        """
        Validate that date is after a specific date.

        Args:
            value: Date value to validate
            after_date: Date that value must be after
            field_name: Name of the field for error message

        Returns:
            The value if valid

        Raises:
            ValidationError: If date is not after the specified date
        """
        check_value = value.date() if isinstance(value, datetime) else value
        check_after = after_date.date() if isinstance(after_date, datetime) else after_date
        
        if check_value <= check_after:
            raise ValidationError(
                f"{field_name} must be after {check_after}",
                field=field_name,
                expected=f"> {check_after}",
                actual=check_value
            )
        return value

    @staticmethod
    def custom(
        value: Any,
        validator_func: Callable[[Any], bool],
        field_name: str,
        error_message: str
    ) -> Any:
        """
        Apply a custom validation function.

        Args:
            value: Value to validate
            validator_func: Function that returns True if valid
            field_name: Name of the field for error message
            error_message: Custom error message

        Returns:
            The value if valid

        Raises:
            ValidationError: If validation fails
        """
        if not validator_func(value):
            raise ValidationError(
                error_message,
                field=field_name,
                actual=value
            )
        return value

    @staticmethod
    def validate_notional(value: float, field_name: str = "notional") -> float:
        """Validate trade notional amount."""
        Validators.not_none(value, field_name)
        Validators.positive(value, field_name)
        return value

    @staticmethod
    def validate_rate(value: float, field_name: str = "rate") -> float:
        """Validate interest rate."""
        Validators.not_none(value, field_name)
        return value

    @staticmethod
    def validate_volatility(value: float, field_name: str = "volatility") -> float:
        """Validate volatility (must be non-negative)."""
        Validators.not_none(value, field_name)
        Validators.non_negative(value, field_name)
        return value

    @staticmethod
    def validate_confidence_level(value: float, field_name: str = "confidence_level") -> float:
        """Validate confidence level for risk metrics (typically 0.95 or 0.99)."""
        Validators.not_none(value, field_name)
        Validators.probability(value, field_name)
        return value

    @staticmethod
    def validate_time_horizon(value: float, field_name: str = "time_horizon") -> float:
        """Validate time horizon (must be positive)."""
        Validators.not_none(value, field_name)
        Validators.positive(value, field_name)
        return value
