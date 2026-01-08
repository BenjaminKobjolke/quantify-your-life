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

    # Dynamic yearly data (newest to oldest)
    # Format: ((2026, value), (2025, value), (2024, value), ...)
    yearly_totals: tuple[tuple[int, float], ...] = ()
    # Format: ((2026, %), (2025, %), ...) - first entry is this_year vs last_year
    yoy_percentages: tuple[tuple[int, float | None], ...] = ()

    # Backward-compatible properties (computed from yearly_totals)
    @property
    def total_this_year(self) -> float:
        """Total for current year (backward compatibility)."""
        return self.yearly_totals[0][1] if len(self.yearly_totals) > 0 else 0.0

    @property
    def total_last_year(self) -> float:
        """Total for last year (backward compatibility)."""
        return self.yearly_totals[1][1] if len(self.yearly_totals) > 1 else 0.0

    @property
    def total_year_before(self) -> float:
        """Total for year before last (backward compatibility)."""
        return self.yearly_totals[2][1] if len(self.yearly_totals) > 2 else 0.0

    @property
    def yoy_this_vs_last(self) -> float | None:
        """YoY percentage this year vs last (backward compatibility)."""
        return self.yoy_percentages[0][1] if len(self.yoy_percentages) > 0 else None

    @property
    def yoy_last_vs_year_before(self) -> float | None:
        """YoY percentage last year vs year before (backward compatibility)."""
        return self.yoy_percentages[1][1] if len(self.yoy_percentages) > 1 else None


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

    def calculate(self, get_sum: SumFunction, num_years: int = 3) -> TimeStats:
        """Calculate all statistics using the provided sum function.

        Args:
            get_sum: Function that returns sum of values between dates.
                     Signature: get_sum(start_date, end_date) -> float
                     - start_date: First day to include (inclusive)
                     - end_date: Last day to include (inclusive)
                     - If start_date is None, no lower bound.
                     - If end_date is None, use today.
            num_years: Number of years to calculate totals for (default: 3).

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

        # Last 12 months (calculate actual days for leap year handling)
        last_12_months_sum = get_sum(ranges["12_months_ago"], ranges["today"])
        days_last_12_months = (ranges["today"] - ranges["12_months_ago"]).days + 1
        avg_last_12_months = (
            last_12_months_sum / days_last_12_months if days_last_12_months > 0 else 0.0
        )

        # This year
        this_year_sum = get_sum(ranges["year_start"], ranges["today"])
        days_this_year = (ranges["today"] - ranges["year_start"]).days + 1
        avg_this_year = this_year_sum / days_this_year if days_this_year > 0 else 0.0

        # Last year (calculate actual days for leap year handling)
        last_year_sum = get_sum(ranges["last_year_start"], ranges["last_year_end"])
        days_last_year = (ranges["last_year_end"] - ranges["last_year_start"]).days + 1
        avg_last_year = last_year_sum / days_last_year if days_last_year > 0 else 0.0

        # Standard periods
        this_week = get_sum(ranges["week_start"], ranges["today"])
        this_month = get_sum(ranges["month_start"], ranges["today"])
        last_month = get_sum(ranges["last_month_start"], ranges["last_month_end"])
        total = get_sum(None, None)

        # Calculate N years of totals dynamically
        yearly_totals = self._calculate_yearly_totals(get_sum, num_years)
        yoy_percentages = self._calculate_yoy_percentages(yearly_totals)

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
            yearly_totals=yearly_totals,
            yoy_percentages=yoy_percentages,
        )

    def _calculate_yearly_totals(
        self, get_sum: SumFunction, num_years: int
    ) -> tuple[tuple[int, float], ...]:
        """Calculate totals for N years.

        Args:
            get_sum: Function to get sum for date range.
            num_years: Number of years to calculate.

        Returns:
            Tuple of (year, total) pairs, newest to oldest.
        """
        today = date.today()
        current_year = today.year
        yearly_totals: list[tuple[int, float]] = []

        for i in range(num_years):
            year = current_year - i
            if i == 0:
                # Current year: from Jan 1 to today
                year_start = date(year, 1, 1)
                year_end = today
            else:
                # Past years: full year
                year_start = date(year, 1, 1)
                year_end = date(year, 12, 31)

            year_sum = get_sum(year_start, year_end)
            yearly_totals.append((year, year_sum))

        return tuple(yearly_totals)

    def _calculate_yoy_percentages(
        self, yearly_totals: tuple[tuple[int, float], ...]
    ) -> tuple[tuple[int, float | None], ...]:
        """Calculate year-over-year percentages from yearly totals.

        Args:
            yearly_totals: Tuple of (year, total) pairs, newest to oldest.

        Returns:
            Tuple of (year, percentage) pairs for each comparison.
            Entry at index i compares year[i] vs year[i+1].
        """
        yoy_percentages: list[tuple[int, float | None]] = []

        for i in range(len(yearly_totals) - 1):
            current_year, current_total = yearly_totals[i]
            _, previous_total = yearly_totals[i + 1]
            pct = self._calculate_trend(current_total, previous_total)
            yoy_percentages.append((current_year, pct))

        return tuple(yoy_percentages)

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

        # Year before last
        year_before_start = date(today.year - 2, 1, 1)
        year_before_end = date(today.year - 2, 12, 31)

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
            "year_before_start": year_before_start,
            "year_before_end": year_before_end,
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
