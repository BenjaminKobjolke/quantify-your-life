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

    # Export config menu
    EXPORT_MENU_TITLE: str = "What would you like to do?"
    EXPORT_MENU_ADD: str = "Add entry"
    EXPORT_MENU_REMOVE: str = "Remove entry"
    EXPORT_MENU_SET_PATH: str = "Set export path"
    EXPORT_MENU_EXIT: str = "Exit"

    EXPORT_TYPE_TITLE: str = "What type to add?"
    EXPORT_TYPE_GROUP: str = "Group"
    EXPORT_TYPE_FEATURE: str = "Feature"

    EXPORT_SELECT_GROUP: str = "Select a group:"
    EXPORT_SELECT_FEATURE: str = "Select a feature:"
    EXPORT_SELECT_REMOVE: str = "Select entry to remove:"
    EXPORT_ENTER_PATH: str = "Enter export path:"

    # Export messages
    EXPORT_ADDED_GROUP: str = 'Added group "{name}" (ID {id}) to export config'
    EXPORT_ADDED_FEATURE: str = 'Added feature "{name}" (ID {id}) to export config'
    EXPORT_REMOVED: str = 'Removed "{name}" from export config'
    EXPORT_PATH_SET: str = "Export path set to: {path}"
    EXPORT_NO_ENTRIES: str = "No entries configured for export"
    EXPORT_NO_PATH: str = "No export path configured. Please set export path first."
    EXPORT_SUCCESS: str = "Exported {count} file(s) to {path}"
    EXPORT_GROUP_NOT_FOUND: str = "Group ID {id} not found"
    EXPORT_FEATURE_NOT_FOUND: str = "Feature ID {id} not found"
    EXPORT_ALREADY_EXISTS: str = '"{name}" is already in export config'

    # Export labels
    EXPORT_LABEL_GROUP: str = "Group: {name} (ID {id})"
    EXPORT_LABEL_FEATURE: str = "Feature: {name} (ID {id})"
    EXPORT_LABEL_STATS: str = "{source}: {name}"

    # Source selection
    SOURCE_SELECT_TITLE: str = "Select data source:"
    SOURCE_NO_CONFIGURED: str = "No data sources are configured"
    SOURCE_TRACK_AND_GRAPH: str = "Track & Graph"
    SOURCE_HOMETRAINER: str = "Hometrainer"

    # Hometrainer
    HOMETRAINER_STATS_NAME: str = "Hometrainer"

    # Main menu options
    MENU_VIEW_STATS: str = "View Statistics"
    MENU_TOP_REPOS: str = "Top 10 Repos"
    MENU_DEBUG_GIT: str = "Debug Git Exclusions"
    MENU_BACK: str = "← Back"
    MENU_EXIT: str = "Exit"

    # Git Stats menu
    GIT_SELECT_PERIOD: str = "Select time period:"
    GIT_PERIOD_LAST_7_DAYS: str = "Last 7 days"
    GIT_PERIOD_LAST_30_DAYS: str = "Last 30 days"
    GIT_PERIOD_LAST_12_MONTHS: str = "Last 12 months"
    GIT_PERIOD_ALL_TIME: str = "All time"

    # Debug menu
    DEBUG_SELECT_REPO: str = "Select a repository to analyze:"
    DEBUG_REPORT_TITLE: str = "Exclusion Report"
    DEBUG_TOTAL_TRACKED: str = "Total tracked files"
    DEBUG_EXCLUDED_DIR: str = "Excluded by directory"
    DEBUG_EXCLUDED_EXT: str = "Excluded by extension"
    DEBUG_EXCLUDED_NAME: str = "Excluded by filename"
    DEBUG_INCLUDED: str = "Files to be counted"
