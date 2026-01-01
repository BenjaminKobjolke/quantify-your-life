"""String constants for the application."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Constants:
    """Centralized string constants."""

    # Menu options
    MENU_VIEW_BY: str = "How would you like to view statistics?"
    MENU_GROUP: str = "By Group"
    MENU_FEATURE: str = "By Feature"
    MENU_SELECT_GROUP: str = "Select a group:"
    MENU_SELECT_FEATURE: str = "Select a feature:"

    # Time period labels
    PERIOD_LAST_7_DAYS: str = "Last 7 days"
    PERIOD_LAST_31_DAYS: str = "Last 31 days"
    PERIOD_AVG_LAST_30_DAYS: str = "Avg/day (last 30 days)"
    PERIOD_TREND_30_DAYS: str = "vs previous 30 days"
    PERIOD_AVG_LAST_12_MONTHS: str = "Avg/day (last 12 months)"
    PERIOD_AVG_THIS_YEAR: str = "Avg/day (this year)"
    PERIOD_AVG_LAST_YEAR: str = "Avg/day (last year)"
    PERIOD_THIS_WEEK: str = "This week"
    PERIOD_THIS_MONTH: str = "This month"
    PERIOD_LAST_MONTH: str = "Last month"
    PERIOD_LAST_12_MONTHS: str = "Last 12 months"
    PERIOD_TOTAL: str = "Total"

    # Output labels
    LABEL_STATISTICS_FOR: str = "Statistics for"
    LABEL_NO_DATA: str = "No data available"

    # Error messages
    ERROR_CONFIG_NOT_FOUND: str = "Config file not found: {path}"
    ERROR_DB_NOT_FOUND: str = "Database file not found: {path}"
    ERROR_NO_GROUPS: str = "No groups found in database"
    ERROR_NO_FEATURES: str = "No features found in database"

    # Config
    CONFIG_FILE_NAME: str = "config.json"
