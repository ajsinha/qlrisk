"""
Date Utilities - Date manipulation utilities for QLRisk

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from enum import Enum
import calendar


class DayCountConvention(Enum):
    """Day count conventions for interest rate calculations."""
    ACT_360 = "ACT/360"
    ACT_365 = "ACT/365"
    ACT_365F = "ACT/365F"
    ACT_ACT = "ACT/ACT"
    THIRTY_360 = "30/360"
    THIRTY_360E = "30E/360"
    BUS_252 = "BUS/252"


class BusinessDayConvention(Enum):
    """Business day adjustment conventions."""
    FOLLOWING = "following"
    MODIFIED_FOLLOWING = "modified_following"
    PRECEDING = "preceding"
    MODIFIED_PRECEDING = "modified_preceding"
    UNADJUSTED = "unadjusted"


class DateUtils:
    """
    Utility class for date operations commonly used in financial calculations.
    """

    # Standard holidays (simplified - in production, use proper holiday calendars)
    _WEEKENDS = {5, 6}  # Saturday = 5, Sunday = 6

    @staticmethod
    def today() -> date:
        """Get today's date."""
        return date.today()

    @staticmethod
    def now() -> datetime:
        """Get current datetime."""
        return datetime.now()

    @staticmethod
    def parse_date(date_str: str, format_str: str = "%Y-%m-%d") -> date:
        """
        Parse date string to date object.

        Args:
            date_str: Date string
            format_str: Format string

        Returns:
            Date object
        """
        return datetime.strptime(date_str, format_str).date()

    @staticmethod
    def format_date(d: Union[date, datetime], format_str: str = "%Y-%m-%d") -> str:
        """
        Format date to string.

        Args:
            d: Date or datetime object
            format_str: Format string

        Returns:
            Formatted date string
        """
        return d.strftime(format_str)

    @staticmethod
    def is_business_day(d: Union[date, datetime]) -> bool:
        """
        Check if date is a business day (not weekend).

        Args:
            d: Date to check

        Returns:
            True if business day
        """
        check_date = d.date() if isinstance(d, datetime) else d
        return check_date.weekday() not in DateUtils._WEEKENDS

    @staticmethod
    def next_business_day(d: Union[date, datetime]) -> date:
        """
        Get next business day.

        Args:
            d: Starting date

        Returns:
            Next business day
        """
        check_date = d.date() if isinstance(d, datetime) else d
        next_day = check_date + timedelta(days=1)
        
        while not DateUtils.is_business_day(next_day):
            next_day += timedelta(days=1)
        
        return next_day

    @staticmethod
    def previous_business_day(d: Union[date, datetime]) -> date:
        """
        Get previous business day.

        Args:
            d: Starting date

        Returns:
            Previous business day
        """
        check_date = d.date() if isinstance(d, datetime) else d
        prev_day = check_date - timedelta(days=1)
        
        while not DateUtils.is_business_day(prev_day):
            prev_day -= timedelta(days=1)
        
        return prev_day

    @staticmethod
    def adjust_business_day(
        d: Union[date, datetime],
        convention: BusinessDayConvention = BusinessDayConvention.MODIFIED_FOLLOWING
    ) -> date:
        """
        Adjust date according to business day convention.

        Args:
            d: Date to adjust
            convention: Business day convention

        Returns:
            Adjusted date
        """
        check_date = d.date() if isinstance(d, datetime) else d
        
        if DateUtils.is_business_day(check_date):
            return check_date
        
        if convention == BusinessDayConvention.UNADJUSTED:
            return check_date
        
        if convention == BusinessDayConvention.FOLLOWING:
            return DateUtils.next_business_day(check_date)
        
        if convention == BusinessDayConvention.PRECEDING:
            return DateUtils.previous_business_day(check_date)
        
        if convention == BusinessDayConvention.MODIFIED_FOLLOWING:
            adjusted = DateUtils.next_business_day(check_date)
            # If crosses month boundary, use previous business day
            if adjusted.month != check_date.month:
                adjusted = DateUtils.previous_business_day(check_date)
            return adjusted
        
        if convention == BusinessDayConvention.MODIFIED_PRECEDING:
            adjusted = DateUtils.previous_business_day(check_date)
            # If crosses month boundary, use next business day
            if adjusted.month != check_date.month:
                adjusted = DateUtils.next_business_day(check_date)
            return adjusted
        
        return check_date

    @staticmethod
    def year_fraction(
        start_date: Union[date, datetime],
        end_date: Union[date, datetime],
        convention: DayCountConvention = DayCountConvention.ACT_365
    ) -> float:
        """
        Calculate year fraction between two dates.

        Args:
            start_date: Start date
            end_date: End date
            convention: Day count convention

        Returns:
            Year fraction
        """
        d1 = start_date.date() if isinstance(start_date, datetime) else start_date
        d2 = end_date.date() if isinstance(end_date, datetime) else end_date
        
        days = (d2 - d1).days
        
        if convention == DayCountConvention.ACT_360:
            return days / 360.0
        
        if convention in (DayCountConvention.ACT_365, DayCountConvention.ACT_365F):
            return days / 365.0
        
        if convention == DayCountConvention.ACT_ACT:
            # Simplified ACT/ACT implementation
            year1 = d1.year
            year2 = d2.year
            
            if year1 == year2:
                days_in_year = 366 if calendar.isleap(year1) else 365
                return days / days_in_year
            
            # Handle multi-year periods
            total_fraction = 0.0
            current = d1
            
            for year in range(year1, year2 + 1):
                year_start = date(year, 1, 1)
                year_end = date(year, 12, 31)
                days_in_year = 366 if calendar.isleap(year) else 365
                
                period_start = max(current, year_start)
                period_end = min(d2, year_end)
                
                if period_end >= period_start:
                    period_days = (period_end - period_start).days
                    total_fraction += period_days / days_in_year
                
                current = date(year + 1, 1, 1)
            
            return total_fraction
        
        if convention == DayCountConvention.THIRTY_360:
            d1_day = min(d1.day, 30)
            d2_day = min(d2.day, 30) if d1_day == 30 else d2.day
            
            return (
                360 * (d2.year - d1.year) +
                30 * (d2.month - d1.month) +
                (d2_day - d1_day)
            ) / 360.0
        
        if convention == DayCountConvention.THIRTY_360E:
            d1_day = min(d1.day, 30)
            d2_day = min(d2.day, 30)
            
            return (
                360 * (d2.year - d1.year) +
                30 * (d2.month - d1.month) +
                (d2_day - d1_day)
            ) / 360.0
        
        # Default to ACT/365
        return days / 365.0

    @staticmethod
    def add_months(d: Union[date, datetime], months: int) -> date:
        """
        Add months to a date.

        Args:
            d: Starting date
            months: Number of months to add (can be negative)

        Returns:
            New date
        """
        check_date = d.date() if isinstance(d, datetime) else d
        
        year = check_date.year
        month = check_date.month + months
        
        while month > 12:
            month -= 12
            year += 1
        
        while month < 1:
            month += 12
            year -= 1
        
        # Handle day overflow (e.g., Jan 31 + 1 month)
        day = min(check_date.day, calendar.monthrange(year, month)[1])
        
        return date(year, month, day)

    @staticmethod
    def add_years(d: Union[date, datetime], years: int) -> date:
        """
        Add years to a date.

        Args:
            d: Starting date
            years: Number of years to add (can be negative)

        Returns:
            New date
        """
        return DateUtils.add_months(d, years * 12)

    @staticmethod
    def generate_schedule(
        start_date: Union[date, datetime],
        end_date: Union[date, datetime],
        frequency_months: int = 3,
        convention: BusinessDayConvention = BusinessDayConvention.MODIFIED_FOLLOWING
    ) -> List[date]:
        """
        Generate a payment schedule.

        Args:
            start_date: Start date
            end_date: End date
            frequency_months: Payment frequency in months
            convention: Business day convention

        Returns:
            List of payment dates
        """
        d1 = start_date.date() if isinstance(start_date, datetime) else start_date
        d2 = end_date.date() if isinstance(end_date, datetime) else end_date
        
        schedule = []
        current = d1
        
        while current <= d2:
            adjusted = DateUtils.adjust_business_day(current, convention)
            if adjusted <= d2:
                schedule.append(adjusted)
            current = DateUtils.add_months(current, frequency_months)
        
        # Ensure end date is included
        adjusted_end = DateUtils.adjust_business_day(d2, convention)
        if schedule and schedule[-1] != adjusted_end:
            schedule.append(adjusted_end)
        
        return schedule

    @staticmethod
    def business_days_between(
        start_date: Union[date, datetime],
        end_date: Union[date, datetime]
    ) -> int:
        """
        Count business days between two dates.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Number of business days
        """
        d1 = start_date.date() if isinstance(start_date, datetime) else start_date
        d2 = end_date.date() if isinstance(end_date, datetime) else end_date
        
        count = 0
        current = d1
        
        while current < d2:
            if DateUtils.is_business_day(current):
                count += 1
            current += timedelta(days=1)
        
        return count

    @staticmethod
    def end_of_month(d: Union[date, datetime]) -> date:
        """
        Get end of month for a given date.

        Args:
            d: Date

        Returns:
            Last day of the month
        """
        check_date = d.date() if isinstance(d, datetime) else d
        _, last_day = calendar.monthrange(check_date.year, check_date.month)
        return date(check_date.year, check_date.month, last_day)

    @staticmethod
    def start_of_month(d: Union[date, datetime]) -> date:
        """
        Get start of month for a given date.

        Args:
            d: Date

        Returns:
            First day of the month
        """
        check_date = d.date() if isinstance(d, datetime) else d
        return date(check_date.year, check_date.month, 1)

    @staticmethod
    def is_end_of_month(d: Union[date, datetime]) -> bool:
        """
        Check if date is end of month.

        Args:
            d: Date to check

        Returns:
            True if end of month
        """
        check_date = d.date() if isinstance(d, datetime) else d
        return check_date == DateUtils.end_of_month(check_date)

    @staticmethod
    def days_in_year(year: int) -> int:
        """
        Get number of days in a year.

        Args:
            year: Year

        Returns:
            365 or 366
        """
        return 366 if calendar.isleap(year) else 365
