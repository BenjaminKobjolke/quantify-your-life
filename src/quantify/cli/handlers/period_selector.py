"""Time period selection utilities for git stats."""

from datetime import date, timedelta

import questionary

from quantify.config.constants import Constants
from quantify.services.stats_calculator import TimeStats

# Period key constants
PERIOD_LAST_7_DAYS = "last_7_days"
PERIOD_LAST_30_DAYS = "last_30_days"
PERIOD_LAST_12_MONTHS = "last_12_months"
PERIOD_THIS_YEAR = "this_year"
PERIOD_LAST_YEAR = "last_year"
PERIOD_YEAR_BEFORE = "year_before"
PERIOD_ALL_TIME = "all_time"


def get_period_choices() -> list[questionary.Choice]:
    """Build period selection choices with year labels.

    Returns:
        List of questionary choices for period selection.
    """
    current_year = date.today().year
    return [
        questionary.Choice(title=Constants.GIT_PERIOD_LAST_7_DAYS, value=PERIOD_LAST_7_DAYS),
        questionary.Choice(title=Constants.GIT_PERIOD_LAST_30_DAYS, value=PERIOD_LAST_30_DAYS),
        questionary.Choice(title=Constants.GIT_PERIOD_LAST_12_MONTHS, value=PERIOD_LAST_12_MONTHS),
        questionary.Choice(
            title=Constants.GIT_PERIOD_THIS_YEAR.format(year=current_year),
            value=PERIOD_THIS_YEAR,
        ),
        questionary.Choice(
            title=Constants.GIT_PERIOD_LAST_YEAR.format(year=current_year - 1),
            value=PERIOD_LAST_YEAR,
        ),
        questionary.Choice(
            title=Constants.GIT_PERIOD_YEAR_BEFORE.format(year=current_year - 2),
            value=PERIOD_YEAR_BEFORE,
        ),
        questionary.Choice(title=Constants.GIT_PERIOD_ALL_TIME, value=PERIOD_ALL_TIME),
        questionary.Choice(title=Constants.MENU_BACK, value=None),
    ]


def get_period_date_range(period_key: str) -> tuple[date | None, date]:
    """Get date range for a period key.

    Args:
        period_key: Internal period key constant.

    Returns:
        Tuple of (start_date, end_date). start_date is None for all time.
    """
    today = date.today()
    current_year = today.year

    if period_key == PERIOD_LAST_7_DAYS:
        return today - timedelta(days=6), today
    elif period_key == PERIOD_LAST_30_DAYS:
        return today - timedelta(days=29), today
    elif period_key == PERIOD_LAST_12_MONTHS:
        return today - timedelta(days=364), today
    elif period_key == PERIOD_THIS_YEAR:
        return date(current_year, 1, 1), today
    elif period_key == PERIOD_LAST_YEAR:
        return date(current_year - 1, 1, 1), date(current_year - 1, 12, 31)
    elif period_key == PERIOD_YEAR_BEFORE:
        return date(current_year - 2, 1, 1), date(current_year - 2, 12, 31)
    else:  # ALL_TIME
        return None, today


def get_period_label(period_key: str) -> str:
    """Get display label for a period key.

    Args:
        period_key: Internal period key constant.

    Returns:
        Human-readable period label.
    """
    current_year = date.today().year

    if period_key == PERIOD_LAST_7_DAYS:
        return Constants.GIT_PERIOD_LAST_7_DAYS
    elif period_key == PERIOD_LAST_30_DAYS:
        return Constants.GIT_PERIOD_LAST_30_DAYS
    elif period_key == PERIOD_LAST_12_MONTHS:
        return Constants.GIT_PERIOD_LAST_12_MONTHS
    elif period_key == PERIOD_THIS_YEAR:
        return Constants.GIT_PERIOD_THIS_YEAR.format(year=current_year)
    elif period_key == PERIOD_LAST_YEAR:
        return Constants.GIT_PERIOD_LAST_YEAR.format(year=current_year - 1)
    elif period_key == PERIOD_YEAR_BEFORE:
        return Constants.GIT_PERIOD_YEAR_BEFORE.format(year=current_year - 2)
    else:
        return Constants.GIT_PERIOD_ALL_TIME


def get_stat_value_for_period(stats: TimeStats, period_key: str) -> float:
    """Extract the stat value for a specific period from TimeStats.

    Args:
        stats: TimeStats object with all calculated periods.
        period_key: Internal period key constant.

    Returns:
        The stat value for the specified period.
    """
    if period_key == PERIOD_LAST_7_DAYS:
        return stats.last_7_days
    elif period_key == PERIOD_LAST_30_DAYS:
        return stats.last_31_days  # Using 31 days as closest match
    elif period_key == PERIOD_LAST_12_MONTHS:
        return stats.last_12_months
    elif period_key == PERIOD_THIS_YEAR:
        return stats.total_this_year
    elif period_key == PERIOD_LAST_YEAR:
        return stats.total_last_year
    elif period_key == PERIOD_YEAR_BEFORE:
        return stats.total_year_before
    else:  # ALL_TIME
        return stats.total


def select_period() -> str | None:
    """Prompt user to select a time period.

    Returns:
        Selected period key or None if cancelled.
    """
    return questionary.select(
        Constants.GIT_SELECT_PERIOD,
        choices=get_period_choices(),
    ).ask()
