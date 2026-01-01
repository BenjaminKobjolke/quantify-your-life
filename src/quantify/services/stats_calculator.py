"""Shared statistics calculator for all data sources.

This is the SINGLE SOURCE OF TRUTH for all time period calculations.
To add/remove time periods, modify this file only.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class TimeStats:
    """Time statistics for all time periods. Used by ALL sources."""

    # Recent periods
    last_7_days: float
    last_31_days: float

    # Averages
    avg_per_day_last_30_days: float
    trend_vs_previous_30_days: float | None  # Percentage, None if no previous data
    avg_per_day_last_12_months: float
    avg_per_day_this_year: float
    avg_per_day_last_year: float

    # Standard periods
    this_week: float
    this_month: float
    last_month: float
    last_12_months: float
    total: float


# Type alias for the sum function that sources provide
SumFunction = Callable[[date | None, date | None], float]


class StatsCalculator:
    """Centralized stats calculation for all data sources.

    Sources provide a `get_sum(start_date, end_date)` function,
    and this calculator handles all the time period logic.

    Example usage:
        def my_source_get_sum(start: date | None, end: date | None) -> float:
            # Query your data source
            return sum_value

        calculator = StatsCalculator()
        stats = calculator.calculate(my_source_get_sum)
    """

    def calculate(self, get_sum: SumFunction) -> TimeStats:
        """Calculate all statistics using the provided sum function.

        Args:
            get_sum: Function that returns sum of values between dates.
                     Signature: get_sum(start_date, end_date) -> float
                     - start_date: First day to include (inclusive)
                     - end_date: Last day to include (inclusive)
                     - If start_date is None, no lower bound.
                     - If end_date is None, use today.

        Returns:
            TimeStats with all calculated periods.
        """
        ranges = self._get_date_ranges()

        # Recent periods
        last_7_days = get_sum(ranges["7_days_ago"], ranges["today"])
        last_31_days = get_sum(ranges["31_days_ago"], ranges["today"])

        # Last 30 days and previous 30 days for trend
        last_30_days = get_sum(ranges["30_days_ago"], ranges["today"])
        previous_30_days = get_sum(ranges["60_days_ago"], ranges["31_days_ago"])

        # Averages
        avg_last_30 = last_30_days / 30 if last_30_days else 0.0
        trend = self._calculate_trend(last_30_days, previous_30_days)

        # Last 12 months
        last_12_months_sum = get_sum(ranges["12_months_ago"], ranges["today"])
        avg_last_12_months = last_12_months_sum / 365 if last_12_months_sum else 0.0

        # This year
        this_year_sum = get_sum(ranges["year_start"], ranges["today"])
        days_this_year = (ranges["today"] - ranges["year_start"]).days + 1
        avg_this_year = this_year_sum / days_this_year if days_this_year > 0 else 0.0

        # Last year
        last_year_sum = get_sum(ranges["last_year_start"], ranges["last_year_end"])
        avg_last_year = last_year_sum / 365 if last_year_sum else 0.0

        # Standard periods
        this_week = get_sum(ranges["week_start"], ranges["today"])
        this_month = get_sum(ranges["month_start"], ranges["today"])
        last_month = get_sum(ranges["last_month_start"], ranges["last_month_end"])
        total = get_sum(None, None)

        return TimeStats(
            last_7_days=last_7_days,
            last_31_days=last_31_days,
            avg_per_day_last_30_days=avg_last_30,
            trend_vs_previous_30_days=trend,
            avg_per_day_last_12_months=avg_last_12_months,
            avg_per_day_this_year=avg_this_year,
            avg_per_day_last_year=avg_last_year,
            this_week=this_week,
            this_month=this_month,
            last_month=last_month,
            last_12_months=last_12_months_sum,
            total=total,
        )

    def _get_date_ranges(self) -> dict[str, date]:
        """Calculate all date boundaries.

        This is the SINGLE SOURCE OF TRUTH for all time periods.
        To add a new time period:
        1. Add the date calculation here
        2. Add the field to TimeStats
        3. Add the calculation in calculate()

        Returns:
            Dictionary with date values for various time boundaries.
        """
        today = date.today()

        # Recent day ranges
        days_7_ago = today - timedelta(days=7)
        days_30_ago = today - timedelta(days=30)
        days_31_ago = today - timedelta(days=31)
        days_60_ago = today - timedelta(days=60)

        # Start of this week (Monday)
        week_start = today - timedelta(days=today.weekday())

        # Start of this month
        month_start = today.replace(day=1)

        # Last month boundaries
        last_month_end = month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        # 12 months ago
        months_12_ago = today - timedelta(days=365)

        # This year
        year_start = date(today.year, 1, 1)

        # Last year
        last_year_start = date(today.year - 1, 1, 1)
        last_year_end = date(today.year - 1, 12, 31)

        return {
            "today": today,
            "7_days_ago": days_7_ago,
            "30_days_ago": days_30_ago,
            "31_days_ago": days_31_ago,
            "60_days_ago": days_60_ago,
            "week_start": week_start,
            "month_start": month_start,
            "last_month_start": last_month_start,
            "last_month_end": last_month_end,
            "12_months_ago": months_12_ago,
            "year_start": year_start,
            "last_year_start": last_year_start,
            "last_year_end": last_year_end,
        }

    def _calculate_trend(self, current: float, previous: float) -> float | None:
        """Calculate percentage change between two periods.

        Args:
            current: Current period value.
            previous: Previous period value.

        Returns:
            Percentage change or None if previous is zero.
        """
        if previous <= 0:
            return None
        return ((current - previous) / previous) * 100
