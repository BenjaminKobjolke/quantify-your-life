"""CLI module."""

from quantify.cli.formatting import (
    format_commits,
    format_distance,
    format_duration,
    format_lines,
    format_projects,
    format_trend,
)
from quantify.cli.menu import Menu

__all__ = [
    "Menu",
    "format_commits",
    "format_distance",
    "format_duration",
    "format_lines",
    "format_projects",
    "format_trend",
]
