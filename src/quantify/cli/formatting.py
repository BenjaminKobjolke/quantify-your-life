"""Formatting functions for CLI display."""


def format_duration(seconds: float) -> str:
    """Format seconds as human-readable duration.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string like "5h 23m" or "45m".
    """
    if seconds <= 0:
        return "0m"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def format_distance(value: float, unit: str) -> str:
    """Format distance value.

    Args:
        value: Distance value.
        unit: Unit label (km, mi).

    Returns:
        Formatted string like "42.5 km".
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
    """Format commit count.

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
    """Format project count.

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


def format_trend(trend: float | None) -> str:
    """Format trend percentage.

    Args:
        trend: Percentage change or None.

    Returns:
        Formatted string like "+15.2%" or "-5.0%" or "N/A".
    """
    if trend is None:
        return "N/A"
    sign = "+" if trend >= 0 else ""
    return f"{sign}{trend:.1f}%"
