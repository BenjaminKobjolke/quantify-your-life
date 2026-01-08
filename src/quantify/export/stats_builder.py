"""Stats data builders for HTML export."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from quantify.config.constants import Constants
from quantify.services.stats import TimeStats, format_trend, format_value
from quantify.sources.base import DisplayConfig


@dataclass
class StatsRow:
    """A row in the stats table."""

    period: str
    value: str
    is_separator: bool = False
    trend_class: str = ""
    key: str = ""  # Row key for filtering


def build_stats_rows(
    stats: TimeStats,
    unit: str,
    unit_label: str,
    display_config: DisplayConfig | None = None,
) -> list[StatsRow]:
    """Build stats table rows from TimeStats.

    Args:
        stats: Statistics data.
        unit: Unit type ("time" or "distance").
        unit_label: Unit label for display.
        display_config: Optional display configuration for filtering rows.

    Returns:
        List of stats rows for the template.
    """
    hide_rows: Sequence[str] = display_config.hide_rows if display_config else ()
    show_rows: Sequence[str] = display_config.show_rows if display_config else ()

    def fmt(value: float) -> str:
        return format_value(value, unit, unit_label)

    def fmt_avg(value: float) -> str:
        return format_value(value, unit, unit_label, is_avg=True)

    def should_show(key: str) -> bool:
        return key not in hide_rows

    # Define all rows with their keys
    all_rows: list[tuple[str, StatsRow]] = [
        # Recent periods
        (
            "last_7_days",
            StatsRow(Constants.PERIOD_LAST_7_DAYS, fmt(stats.last_7_days), key="last_7_days"),
        ),
        (
            "last_31_days",
            StatsRow(Constants.PERIOD_LAST_31_DAYS, fmt(stats.last_31_days), key="last_31_days"),
        ),
        ("_sep1", StatsRow("", "", is_separator=True)),
        # Averages
        ("avg_per_day_last_30_days", StatsRow(
            Constants.PERIOD_AVG_LAST_30_DAYS,
            fmt_avg(stats.avg_per_day_last_30_days),
            key="avg_per_day_last_30_days",
        )),
        ("trend_vs_previous_30_days", _build_trend_row(stats)),
        ("_sep2", StatsRow("", "", is_separator=True)),
        ("avg_per_day_last_12_months", StatsRow(
            Constants.PERIOD_AVG_LAST_12_MONTHS,
            fmt_avg(stats.avg_per_day_last_12_months),
            key="avg_per_day_last_12_months",
        )),
        ("avg_per_day_this_year", StatsRow(
            Constants.PERIOD_AVG_THIS_YEAR,
            fmt_avg(stats.avg_per_day_this_year),
            key="avg_per_day_this_year",
        )),
        ("avg_per_day_last_year", StatsRow(
            Constants.PERIOD_AVG_LAST_YEAR,
            fmt_avg(stats.avg_per_day_last_year),
            key="avg_per_day_last_year",
        )),
        ("_sep3", StatsRow("", "", is_separator=True)),
    ]

    # Build yearly totals dynamically from stats.yearly_totals
    show_all_yoy = display_config.show_all_yoy if display_config else False
    yearly_rows = _build_yearly_rows(stats, fmt, show_rows, show_all_yoy)
    all_rows.extend(yearly_rows)

    all_rows.append(("_sep4", StatsRow("", "", is_separator=True)))

    # Standard periods
    all_rows.extend([
        (
            "this_week",
            StatsRow(Constants.PERIOD_THIS_WEEK, fmt(stats.this_week), key="this_week"),
        ),
        (
            "this_month",
            StatsRow(Constants.PERIOD_THIS_MONTH, fmt(stats.this_month), key="this_month"),
        ),
        (
            "last_month",
            StatsRow(Constants.PERIOD_LAST_MONTH, fmt(stats.last_month), key="last_month"),
        ),
        (
            "last_12_months",
            StatsRow(
                Constants.PERIOD_LAST_12_MONTHS, fmt(stats.last_12_months), key="last_12_months"
            ),
        ),
        ("total", StatsRow(Constants.PERIOD_TOTAL, fmt(stats.total), key="total")),
    ])

    # Filter rows
    rows: list[StatsRow] = []
    prev_was_separator = True  # Start as True to avoid leading separator

    for key, row in all_rows:
        if row.is_separator:
            # Only add separator if previous row wasn't a separator
            if not prev_was_separator:
                rows.append(row)
                prev_was_separator = True
        elif should_show(key):
            rows.append(row)
            prev_was_separator = False

    # Remove trailing separator
    if rows and rows[-1].is_separator:
        rows.pop()

    return rows


def _build_yearly_rows(
    stats: TimeStats,
    fmt: Callable[[float], str],
    show_rows: Sequence[str],
    show_all_yoy: bool = False,
) -> list[tuple[str, StatsRow]]:
    """Build yearly total rows dynamically from stats.yearly_totals.

    Args:
        stats: Statistics data with yearly_totals and yoy_percentages.
        fmt: Formatting function for values.
        show_rows: Rows to show (for YoY percentages).
        show_all_yoy: If True, show YoY percentage after every year.

    Returns:
        List of (key, StatsRow) tuples for yearly data.
    """
    rows: list[tuple[str, StatsRow]] = []

    # Create a lookup for YoY percentages by year
    yoy_by_year: dict[int, float | None] = {}
    for year, pct in stats.yoy_percentages:
        yoy_by_year[year] = pct

    for idx, (year, total) in enumerate(stats.yearly_totals):
        # Generate row key based on position (for backward compatibility)
        if idx == 0:
            key = "total_this_year"
        elif idx == 1:
            key = "total_last_year"
        elif idx == 2:
            key = "total_year_before"
        else:
            key = f"total_year_{year}"

        # Always use just the year as the label
        label = str(year)

        rows.append((key, StatsRow(label, fmt(total), key=key)))

        # Add YoY row after this year if requested and available
        if year in yoy_by_year:
            yoy_key = f"yoy_{year}"
            if idx + 1 < len(stats.yearly_totals):
                prev_year = stats.yearly_totals[idx + 1][0]
            else:
                prev_year = year - 1

            # Check if we should show this YoY row
            should_show_yoy = show_all_yoy
            if idx == 0:
                should_show_yoy = should_show_yoy or "yoy_this_vs_last" in show_rows
            elif idx == 1:
                should_show_yoy = should_show_yoy or "yoy_last_vs_year_before" in show_rows
            else:
                should_show_yoy = should_show_yoy or f"yoy_{year}" in show_rows

            if should_show_yoy:
                # Use predefined label for first two YoY rows for backward compatibility
                if idx == 0:
                    yoy_label = Constants.PERIOD_YOY_THIS_VS_LAST
                    row_key = "yoy_this_vs_last"
                elif idx == 1:
                    yoy_label = Constants.PERIOD_YOY_LAST_VS_YEAR_BEFORE
                    row_key = "yoy_last_vs_year_before"
                else:
                    yoy_label = f"vs {prev_year}"
                    row_key = yoy_key

                yoy_row = _build_yoy_row(yoy_by_year[year], yoy_label, row_key)
                rows.append((row_key, yoy_row))

    return rows


def _build_trend_row(stats: TimeStats) -> StatsRow:
    """Build the trend row with color class."""
    trend_str = format_trend(stats.trend_vs_previous_30_days)
    trend_class = ""
    if stats.trend_vs_previous_30_days is not None:
        is_positive = stats.trend_vs_previous_30_days >= 0
        trend_class = "trend-positive" if is_positive else "trend-negative"
    return StatsRow(
        Constants.PERIOD_TREND_30_DAYS,
        trend_str,
        trend_class=trend_class,
        key="trend_vs_previous_30_days",
    )


def _build_yoy_row(value: float | None, label: str, key: str) -> StatsRow:
    """Build a year-over-year percentage row."""
    trend_str = format_trend(value)
    trend_class = ""
    if value is not None:
        is_positive = value >= 0
        trend_class = "trend-positive" if is_positive else "trend-negative"
    return StatsRow(label, trend_str, trend_class=trend_class, key=key)


def build_chart_data(
    stats: TimeStats,
    display_config: DisplayConfig | None = None,
) -> tuple[list[str], list[float]]:
    """Build chart data from TimeStats.

    Args:
        stats: Statistics data.
        display_config: Optional display configuration with chart settings.

    Returns:
        Tuple of (labels, values) for the chart.
    """
    chart_type = "periods"
    if display_config and display_config.chart:
        chart_type = display_config.chart.chart_type

    if chart_type == "yearly":
        # Yearly totals chart (oldest year first, left to right)
        labels = [str(year) for year, _ in stats.yearly_totals]
        values = [total for _, total in stats.yearly_totals]
        return labels[::-1], values[::-1]

    # Default periods chart
    labels = [
        "Last 7d",
        "This Week",
        "This Month",
        "Last Month",
        "Last 31d",
    ]
    values = [
        stats.last_7_days,
        stats.this_week,
        stats.this_month,
        stats.last_month,
        stats.last_31_days,
    ]
    return labels, values
