"""Interactive CLI menu using questionary."""

from typing import cast

import questionary
from rich.console import Console
from rich.table import Table

from quantify.config.constants import Constants
from quantify.services.stats_calculator import TimeStats
from quantify.sources.base import DataSource, SelectableItem
from quantify.sources.hometrainer import HometrainerSource
from quantify.sources.registry import SourceRegistry
from quantify.sources.track_and_graph import TrackAndGraphSource


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


class Menu:
    """Interactive CLI menu for viewing statistics."""

    def __init__(self, registry: SourceRegistry) -> None:
        """Initialize menu.

        Args:
            registry: Source registry with configured sources.
        """
        self._registry = registry
        self._console = Console()

    def run(self) -> None:
        """Run the interactive menu."""
        # Get configured sources
        sources = self._registry.get_configured_sources()

        if not sources:
            self._console.print(f"[red]{Constants.SOURCE_NO_CONFIGURED}[/red]")
            return

        # Select source (auto-select if only one)
        source = self._select_source(sources)
        if source is None:
            return

        # Handle source-specific flow
        if isinstance(source, TrackAndGraphSource):
            self._handle_track_and_graph(source)
        elif isinstance(source, HometrainerSource):
            self._handle_hometrainer(source)
        else:
            # Generic handling for future sources
            self._handle_generic_source(source)

    def _select_source(self, sources: list[DataSource]) -> DataSource | None:
        """Select a data source.

        Args:
            sources: List of configured sources.

        Returns:
            Selected source or None if cancelled.
        """
        if len(sources) == 1:
            return sources[0]

        choices = [
            questionary.Choice(title=s.info.display_name, value=s) for s in sources
        ]

        result = questionary.select(
            Constants.SOURCE_SELECT_TITLE,
            choices=choices,
        ).ask()

        return cast(DataSource | None, result)

    def _handle_track_and_graph(self, source: TrackAndGraphSource) -> None:
        """Handle Track & Graph source flow."""
        view_choice = self._ask_view_type()
        if view_choice is None:
            return

        if view_choice == Constants.MENU_GROUP:
            items = source.get_groups()
            if not items:
                self._console.print(f"[red]{Constants.ERROR_NO_GROUPS}[/red]")
                return

            selected = self._select_item(items, Constants.MENU_SELECT_GROUP)
            if selected is None:
                return

            stats = source.get_stats(selected.id, "group")
            self._display_stats(selected.name, stats, source.info.unit, source.info.unit_label)
        else:
            items = source.get_features()
            if not items:
                self._console.print(f"[red]{Constants.ERROR_NO_FEATURES}[/red]")
                return

            selected = self._select_item(items, Constants.MENU_SELECT_FEATURE)
            if selected is None:
                return

            stats = source.get_stats(selected.id, "feature")
            self._display_stats(selected.name, stats, source.info.unit, source.info.unit_label)

    def _handle_hometrainer(self, source: HometrainerSource) -> None:
        """Handle Hometrainer source flow."""
        # Hometrainer has single stats, show directly
        items = source.get_selectable_items()
        if items:
            item = items[0]
            stats = source.get_stats(item.id, item.item_type)
            self._display_stats(item.name, stats, source.info.unit, source.info.unit_label)

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
            choices=[Constants.MENU_GROUP, Constants.MENU_FEATURE],
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

    def _display_stats(
        self, name: str, stats: TimeStats, unit: str, unit_label: str
    ) -> None:
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
        def fmt(value: float) -> str:
            if unit == "time":
                return format_duration(value)
            else:
                return format_distance(value, unit_label)

        # Recent periods
        table.add_row(Constants.PERIOD_LAST_7_DAYS, fmt(stats.last_7_days))
        table.add_row(Constants.PERIOD_LAST_31_DAYS, fmt(stats.last_31_days))

        # Averages section
        table.add_row("", "")  # Empty row as separator
        table.add_row(
            Constants.PERIOD_AVG_LAST_30_DAYS,
            fmt(stats.avg_per_day_last_30_days),
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
            fmt(stats.avg_per_day_last_12_months),
        )
        table.add_row(
            Constants.PERIOD_AVG_THIS_YEAR,
            fmt(stats.avg_per_day_this_year),
        )
        table.add_row(
            Constants.PERIOD_AVG_LAST_YEAR,
            fmt(stats.avg_per_day_last_year),
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
