"""Interactive CLI menu using questionary."""

from datetime import date
from typing import cast

import questionary
from rich.console import Console
from rich.table import Table

from quantify.cli.formatting import (
    format_commits,
    format_distance,
    format_duration,
    format_lines,
    format_projects,
    format_trend,
)
from quantify.cli.handlers.git_stats import GitStatsHandler
from quantify.cli.handlers.hometrainer import handle_hometrainer
from quantify.cli.handlers.track_and_graph import handle_track_and_graph
from quantify.config.constants import Constants
from quantify.services.stats_calculator import TimeStats
from quantify.sources.base import DataSource, SelectableItem
from quantify.sources.git_stats import GitStatsSource
from quantify.sources.hometrainer import HometrainerSource
from quantify.sources.registry import SourceRegistry
from quantify.sources.track_and_graph import TrackAndGraphSource


class Menu:
    """Interactive CLI menu for viewing statistics."""

    def __init__(self, registry: SourceRegistry) -> None:
        """Initialize menu.

        Args:
            registry: Source registry with configured sources.
        """
        self._registry = registry
        self._console = Console()
        self._git_stats_handler = GitStatsHandler(self._console, self)

    def run(self) -> None:
        """Run the interactive menu."""
        # Get configured sources
        sources = self._registry.get_configured_sources()

        if not sources:
            self._console.print(f"[red]{Constants.SOURCE_NO_CONFIGURED}[/red]")
            return

        # Main menu loop - back from handlers returns here
        while True:
            # Select source (auto-select if only one)
            source = self._select_source(sources)
            if source is None or isinstance(source, str):
                return  # Exit only when user cancels source selection

            # Handle source-specific flow
            if isinstance(source, TrackAndGraphSource):
                handle_track_and_graph(self._console, source, self)
            elif isinstance(source, HometrainerSource):
                handle_hometrainer(self._console, source, self)
            elif isinstance(source, GitStatsSource):
                self._git_stats_handler.handle(source)
            else:
                # Generic handling for future sources
                self._handle_generic_source(source)
            # When handler returns (back pressed), loop continues to source selection

    def _select_source(self, sources: list[DataSource]) -> DataSource | None:
        """Select a data source.

        Args:
            sources: List of configured sources.

        Returns:
            Selected source or None if cancelled/back.
        """
        if len(sources) == 1:
            return sources[0]

        choices = [questionary.Choice(title=s.info.display_name, value=s) for s in sources]
        choices.append(questionary.Choice(title=Constants.MENU_EXIT, value=None))

        result = questionary.select(
            Constants.SOURCE_SELECT_TITLE,
            choices=choices,
        ).ask()

        return cast(DataSource | None, result)

    def _handle_generic_source(self, source: DataSource) -> None:
        """Handle generic data source flow."""
        items = source.get_selectable_items()

        if not items:
            self._console.print("[yellow]No items available[/yellow]")
            return

        if len(items) == 1:
            # Single item, show directly
            item = items[0]
            stats = source.get_stats(item.id, item.item_type)
            self._display_stats(item.name, stats, source.info.unit, source.info.unit_label)
        else:
            # Multiple items, let user select
            selected = self._select_item(items, "Select item:")
            if selected is None:
                return

            stats = source.get_stats(selected.id, selected.item_type)
            self._display_stats(selected.name, stats, source.info.unit, source.info.unit_label)

    def _ask_view_type(self) -> str | None:
        """Ask user how they want to view statistics.

        Returns:
            Selected view type or None if cancelled.
        """
        result = questionary.select(
            Constants.MENU_VIEW_BY,
            choices=[
                Constants.MENU_GROUP,
                Constants.MENU_FEATURE,
                Constants.MENU_BACK,
            ],
        ).ask()
        return cast(str | None, result)

    def _select_item(self, items: list[SelectableItem], prompt: str) -> SelectableItem | None:
        """Let user select an item.

        Args:
            items: List of available items.
            prompt: Prompt text.

        Returns:
            Selected item or None if cancelled.
        """
        choices = [questionary.Choice(title=item.name, value=item) for item in items]
        result = questionary.select(prompt, choices=choices).ask()
        return cast(SelectableItem | None, result)

    def _select_item_with_back(
        self, items: list[SelectableItem], prompt: str
    ) -> SelectableItem | None:
        """Let user select an item with back option.

        Args:
            items: List of available items.
            prompt: Prompt text.

        Returns:
            Selected item or None if back/cancelled.
        """
        choices = [questionary.Choice(title=item.name, value=item) for item in items]
        choices.append(questionary.Choice(title=Constants.MENU_BACK, value=None))
        result = questionary.select(prompt, choices=choices).ask()
        return cast(SelectableItem | None, result)

    def _display_stats(self, name: str, stats: TimeStats, unit: str, unit_label: str) -> None:
        """Display statistics in a formatted table.

        Args:
            name: Name of the item.
            stats: Statistics to display.
            unit: Unit type ("time" or "distance").
            unit_label: Unit label ("h", "km", "mi").
        """
        table = Table(title=f"{Constants.LABEL_STATISTICS_FOR}: {name}")
        table.add_column("Period", style="cyan")
        table.add_column("Value", style="green", justify="right")

        # Format function based on unit type
        def fmt(value: float, is_avg: bool = False) -> str:
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

        # Recent periods
        table.add_row(Constants.PERIOD_LAST_7_DAYS, fmt(stats.last_7_days))
        table.add_row(Constants.PERIOD_LAST_31_DAYS, fmt(stats.last_31_days))

        # Averages section (show 1 decimal place)
        table.add_row("", "")  # Empty row as separator
        table.add_row(
            Constants.PERIOD_AVG_LAST_30_DAYS,
            fmt(stats.avg_per_day_last_30_days, is_avg=True),
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
            fmt(stats.avg_per_day_last_12_months, is_avg=True),
        )
        table.add_row(
            Constants.PERIOD_AVG_THIS_YEAR,
            fmt(stats.avg_per_day_this_year, is_avg=True),
        )
        table.add_row(
            Constants.PERIOD_AVG_LAST_YEAR,
            fmt(stats.avg_per_day_last_year, is_avg=True),
        )

        # Yearly totals
        table.add_row("", "")  # Empty row as separator
        current_year = date.today().year
        table.add_row(
            Constants.PERIOD_TOTAL_THIS_YEAR.format(year=current_year),
            fmt(stats.total_this_year),
        )
        table.add_row(
            Constants.PERIOD_TOTAL_LAST_YEAR.format(year=current_year - 1),
            fmt(stats.total_last_year),
        )
        table.add_row(
            Constants.PERIOD_TOTAL_YEAR_BEFORE.format(year=current_year - 2),
            fmt(stats.total_year_before),
        )

        # Standard periods
        table.add_row("", "")  # Empty row as separator
        table.add_row(Constants.PERIOD_THIS_WEEK, fmt(stats.this_week))
        table.add_row(Constants.PERIOD_THIS_MONTH, fmt(stats.this_month))
        table.add_row(Constants.PERIOD_LAST_MONTH, fmt(stats.last_month))
        table.add_row(Constants.PERIOD_LAST_12_MONTHS, fmt(stats.last_12_months))
        table.add_row(Constants.PERIOD_TOTAL, fmt(stats.total))

        self._console.print()
        self._console.print(table)
