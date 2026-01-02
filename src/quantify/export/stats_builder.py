"""Stats data builders for HTML export."""

from dataclasses import dataclass
from datetime import date

from quantify.config.constants import Constants
from quantify.services.stats import TimeStats, format_trend, format_value


@dataclass
class StatsRow:
    """A row in the stats table."""

    period: str
    value: str
    is_separator: bool = False
    trend_class: str = ""


def build_stats_rows(stats: TimeStats, unit: str, unit_label: str) -> list[StatsRow]:
    """Build stats table rows from TimeStats.

    Args:
        stats: Statistics data.
        unit: Unit type ("time" or "distance").
        unit_label: Unit label for display.

    Returns:
        List of stats rows for the template.
    """
    rows: list[StatsRow] = []

    def fmt(value: float) -> str:
        return format_value(value, unit, unit_label)

    def fmt_avg(value: float) -> str:
        return format_value(value, unit, unit_label, is_avg=True)

    # Recent periods
    rows.append(StatsRow(Constants.PERIOD_LAST_7_DAYS, fmt(stats.last_7_days)))
    rows.append(StatsRow(Constants.PERIOD_LAST_31_DAYS, fmt(stats.last_31_days)))

    # Separator
    rows.append(StatsRow("", "", is_separator=True))

    # Averages
    rows.append(
        StatsRow(
            Constants.PERIOD_AVG_LAST_30_DAYS,
            fmt_avg(stats.avg_per_day_last_30_days),
        )
    )

    # Trend with color class
    trend_str = format_trend(stats.trend_vs_previous_30_days)
    trend_class = ""
    if stats.trend_vs_previous_30_days is not None:
        is_positive = stats.trend_vs_previous_30_days >= 0
        trend_class = "trend-positive" if is_positive else "trend-negative"
    rows.append(StatsRow(Constants.PERIOD_TREND_30_DAYS, trend_str, trend_class=trend_class))

    # Separator
    rows.append(StatsRow("", "", is_separator=True))

    rows.append(
        StatsRow(
            Constants.PERIOD_AVG_LAST_12_MONTHS,
            fmt_avg(stats.avg_per_day_last_12_months),
        )
    )
    rows.append(
        StatsRow(
            Constants.PERIOD_AVG_THIS_YEAR,
            fmt_avg(stats.avg_per_day_this_year),
        )
    )
    rows.append(
        StatsRow(
            Constants.PERIOD_AVG_LAST_YEAR,
            fmt_avg(stats.avg_per_day_last_year),
        )
    )

    # Separator
    rows.append(StatsRow("", "", is_separator=True))

    # Yearly totals
    current_year = date.today().year
    rows.append(
        StatsRow(
            Constants.PERIOD_TOTAL_THIS_YEAR.format(year=current_year),
            fmt(stats.total_this_year),
        )
    )
    rows.append(
        StatsRow(
            Constants.PERIOD_TOTAL_LAST_YEAR.format(year=current_year - 1),
            fmt(stats.total_last_year),
        )
    )
    rows.append(
        StatsRow(
            Constants.PERIOD_TOTAL_YEAR_BEFORE.format(year=current_year - 2),
            fmt(stats.total_year_before),
        )
    )

    # Separator
    rows.append(StatsRow("", "", is_separator=True))

    # Standard periods
    rows.append(StatsRow(Constants.PERIOD_THIS_WEEK, fmt(stats.this_week)))
    rows.append(StatsRow(Constants.PERIOD_THIS_MONTH, fmt(stats.this_month)))
    rows.append(StatsRow(Constants.PERIOD_LAST_MONTH, fmt(stats.last_month)))
    rows.append(StatsRow(Constants.PERIOD_LAST_12_MONTHS, fmt(stats.last_12_months)))
    rows.append(StatsRow(Constants.PERIOD_TOTAL, fmt(stats.total)))

    return rows


def build_chart_data(stats: TimeStats) -> tuple[list[str], list[float]]:
    """Build chart data from TimeStats.

    Args:
        stats: Statistics data.

    Returns:
        Tuple of (labels, values) for the chart.
    """
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
