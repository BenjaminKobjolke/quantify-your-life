"""Interactive CLI menu using questionary."""

from typing import cast

import questionary
from rich.console import Console
from rich.table import Table

from quantify.config.constants import Constants
from quantify.db.repositories.features import Feature, FeaturesRepository
from quantify.db.repositories.groups import Group, GroupsRepository
from quantify.services.stats import StatsService, TimeStats, format_duration, format_trend


class Menu:
    """Interactive CLI menu for viewing statistics."""

    def __init__(
        self,
        groups_repo: GroupsRepository,
        features_repo: FeaturesRepository,
        stats_service: StatsService,
    ) -> None:
        """Initialize menu.

        Args:
            groups_repo: Repository for groups.
            features_repo: Repository for features.
            stats_service: Service for calculating statistics.
        """
        self._groups = groups_repo
        self._features = features_repo
        self._stats = stats_service
        self._console = Console()

    def run(self) -> None:
        """Run the interactive menu."""
        view_choice = self._ask_view_type()
        if view_choice is None:
            return

        if view_choice == Constants.MENU_GROUP:
            self._handle_group_view()
        else:
            self._handle_feature_view()

    def _ask_view_type(self) -> str | None:
        """Ask user how they want to view statistics.

        Returns:
            Selected view type or None if cancelled.
        """
        result = questionary.select(
            Constants.MENU_VIEW_BY,
            choices=[Constants.MENU_GROUP, Constants.MENU_FEATURE],
        ).ask()
        return cast(str | None, result)

    def _handle_group_view(self) -> None:
        """Handle viewing statistics by group."""
        groups = self._groups.get_all()

        if not groups:
            self._console.print(f"[red]{Constants.ERROR_NO_GROUPS}[/red]")
            return

        selected = self._select_group(groups)
        if selected is None:
            return

        stats = self._stats.get_group_stats(selected.id)
        self._display_stats(selected.name, stats)

    def _handle_feature_view(self) -> None:
        """Handle viewing statistics by feature."""
        features = self._features.get_all()

        if not features:
            self._console.print(f"[red]{Constants.ERROR_NO_FEATURES}[/red]")
            return

        selected = self._select_feature(features)
        if selected is None:
            return

        stats = self._stats.get_feature_stats(selected.id)
        self._display_stats(selected.name, stats)

    def _select_group(self, groups: list[Group]) -> Group | None:
        """Let user select a group.

        Args:
            groups: List of available groups.

        Returns:
            Selected group or None if cancelled.
        """
        choices = [questionary.Choice(title=g.name, value=g) for g in groups]
        result = questionary.select(
            Constants.MENU_SELECT_GROUP,
            choices=choices,
        ).ask()
        return cast(Group | None, result)

    def _select_feature(self, features: list[Feature]) -> Feature | None:
        """Let user select a feature.

        Args:
            features: List of available features.

        Returns:
            Selected feature or None if cancelled.
        """
        choices = [questionary.Choice(title=f.name, value=f) for f in features]
        result = questionary.select(
            Constants.MENU_SELECT_FEATURE,
            choices=choices,
        ).ask()
        return cast(Feature | None, result)

    def _display_stats(self, name: str, stats: TimeStats) -> None:
        """Display statistics in a formatted table.

        Args:
            name: Name of the feature or group.
            stats: Statistics to display.
        """
        table = Table(title=f"{Constants.LABEL_STATISTICS_FOR}: {name}")
        table.add_column("Period", style="cyan")
        table.add_column("Time", style="green", justify="right")

        # Recent periods
        table.add_row(Constants.PERIOD_LAST_7_DAYS, format_duration(stats.last_7_days))
        table.add_row(Constants.PERIOD_LAST_31_DAYS, format_duration(stats.last_31_days))

        # Averages section
        table.add_row("", "")  # Empty row as separator
        table.add_row(
            Constants.PERIOD_AVG_LAST_30_DAYS,
            format_duration(stats.avg_per_day_last_30_days),
        )

        # Trend with color
        trend_str = format_trend(stats.trend_vs_previous_30_days)
        if stats.trend_vs_previous_30_days is not None:
            if stats.trend_vs_previous_30_days >= 0:
                trend_str = f"[green]{trend_str}[/green]"
            else:
                trend_str = f"[red]{trend_str}[/red]"
        table.add_row(Constants.PERIOD_TREND_30_DAYS, trend_str)

        table.add_row("", "")  # Empty row as separator
        table.add_row(
            Constants.PERIOD_AVG_LAST_12_MONTHS,
            format_duration(stats.avg_per_day_last_12_months),
        )
        table.add_row(
            Constants.PERIOD_AVG_THIS_YEAR,
            format_duration(stats.avg_per_day_this_year),
        )
        table.add_row(
            Constants.PERIOD_AVG_LAST_YEAR,
            format_duration(stats.avg_per_day_last_year),
        )

        # Standard periods
        table.add_row("", "")  # Empty row as separator
        table.add_row(Constants.PERIOD_THIS_WEEK, format_duration(stats.this_week))
        table.add_row(Constants.PERIOD_THIS_MONTH, format_duration(stats.this_month))
        table.add_row(Constants.PERIOD_LAST_MONTH, format_duration(stats.last_month))
        table.add_row(Constants.PERIOD_LAST_12_MONTHS, format_duration(stats.last_12_months))
        table.add_row(Constants.PERIOD_TOTAL, format_duration(stats.total))

        self._console.print()
        self._console.print(table)
