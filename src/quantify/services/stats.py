"""Format helpers for statistics display.

Note: The StatsService class has been replaced by the centralized
StatsCalculator in stats_calculator.py. Each data source now uses
the StatsCalculator directly with their own DataProvider.

This module keeps the format helpers for backwards compatibility
and to centralize formatting logic.
"""

from quantify.services.stats_calculator import TimeStats

# Re-export TimeStats for backwards compatibility
__all__ = [
    "TimeStats",
    "format_duration",
    "format_trend",
    "format_distance",
    "format_lines",
    "format_commits",
    "format_projects",
    "format_value",
]


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string like "5h 23m" or "45m" or "0m".
    """
    if seconds <= 0:
        return "0m"

    total_minutes = int(seconds / 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def format_trend(percentage: float | None) -> str:
    """Format trend percentage.

    Args:
        percentage: Percentage change or None.

    Returns:
        Formatted string like "+15.2%" or "-8.3%" or "N/A".
    """
    if percentage is None:
        return "N/A"
    sign = "+" if percentage >= 0 else ""
    return f"{sign}{percentage:.1f}%"


def format_distance(value: float, unit: str) -> str:
    """Format distance value with unit.

    Args:
        value: Distance value.
        unit: Unit label (e.g., "km", "mi").

    Returns:
        Formatted string like "42.5 km" or "10.2 mi".
    """
    return f"{value:.1f} {unit}"


def format_lines(value: float, is_avg: bool = False) -> str:
    """Format line count with thousands separator.

    Args:
        value: Number of lines.
        is_avg: If True, show 1 decimal place for averages.

    Returns:
        Formatted string like "1,234 lines" or "0.9 lines".
    """
    if is_avg:
        return f"{value:,.1f} lines"
    return f"{int(value):,} lines"


def format_commits(value: float, is_avg: bool = False) -> str:
    """Format commit count with thousands separator.

    Args:
        value: Number of commits.
        is_avg: If True, show 1 decimal place for averages.

    Returns:
        Formatted string like "1,234 commits" or "0.9 commits".
    """
    if is_avg:
        return f"{value:,.1f} commits"
    count = int(value)
    suffix = "commit" if count == 1 else "commits"
    return f"{count:,} {suffix}"


def format_projects(value: float, is_avg: bool = False) -> str:
    """Format project count with thousands separator.

    Args:
        value: Number of projects.
        is_avg: If True, show 1 decimal place for averages.

    Returns:
        Formatted string like "15 projects" or "1.5 projects".
    """
    if is_avg:
        return f"{value:,.1f} projects"
    count = int(value)
    suffix = "project" if count == 1 else "projects"
    return f"{count:,} {suffix}"


def format_value(value: float, unit: str, unit_label: str, is_avg: bool = False) -> str:
    """Format a value based on its unit type.

    Args:
        value: The value to format.
        unit: Unit type ("time", "distance", "lines", "commits", or "projects").
        unit_label: Unit label for display (e.g., "h", "km", "mi", "lines").
        is_avg: If True, show decimal places for averages.

    Returns:
        Formatted string appropriate for the unit type.
    """
    if unit == "time":
        return format_duration(value)
    elif unit == "lines":
        return format_lines(value, is_avg)
    elif unit == "commits":
        return format_commits(value, is_avg)
    elif unit == "projects":
        return format_projects(value, is_avg)
    else:
        return format_distance(value, unit_label)
