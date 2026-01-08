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
from quantify.sources.base import DataSource, DisplayConfig, SelectableItem
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

        # Auto-select if only one item
        if len(items) == 1:
            selected = items[0]
            stats = source.get_stats(selected.id, selected.item_type)
            self._display_stats(
                selected.name,
                stats,
                source.info.unit,
                source.info.unit_label,
                source.info.display_config,
            )
            return

        # Multiple items - show selection
        while True:
            selected = self._select_item_with_back(items, "Select item:")
            if selected is None or not isinstance(selected, SelectableItem):
                return

            stats = source.get_stats(selected.id, selected.item_type)
            self._display_stats(
                selected.name,
                stats,
                source.info.unit,
                source.info.unit_label,
                source.info.display_config,
            )

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

    def _display_stats(
        self,
        name: str,
        stats: TimeStats,
        unit: str,
        unit_label: str,
        display_config: DisplayConfig | None = None,
    ) -> None:
        """Display statistics in a formatted table.

        Args:
            name: Name of the item.
            stats: Statistics to display.
            unit: Unit type ("time" or "distance").
            unit_label: Unit label ("h", "km", "mi").
            display_config: Optional display configuration for filtering rows.
        """
        hide_rows = display_config.hide_rows if display_config else ()
        show_rows = display_config.show_rows if display_config else ()

        def should_show(key: str) -> bool:
            return key not in hide_rows

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

        def fmt_trend(value: float | None) -> str:
            trend_str = format_trend(value)
            if value is not None:
                if value >= 0:
                    return f"[green]{trend_str}[/green]"
                else:
                    return f"[red]{trend_str}[/red]"
            return trend_str

        current_year = date.today().year
        rows_added = 0

        def add_separator() -> None:
            nonlocal rows_added
            if rows_added > 0:
                table.add_row("", "")

        def add_row(key: str, label: str, value: str) -> None:
            nonlocal rows_added
            if should_show(key):
                table.add_row(label, value)
                rows_added += 1

        # Recent periods
        add_row("last_7_days", Constants.PERIOD_LAST_7_DAYS, fmt(stats.last_7_days))
        add_row("last_31_days", Constants.PERIOD_LAST_31_DAYS, fmt(stats.last_31_days))

        # Averages section
        add_separator()
        rows_added = 0
        add_row(
            "avg_per_day_last_30_days",
            Constants.PERIOD_AVG_LAST_30_DAYS,
            fmt(stats.avg_per_day_last_30_days, is_avg=True),
        )
        add_row(
            "trend_vs_previous_30_days",
            Constants.PERIOD_TREND_30_DAYS,
            fmt_trend(stats.trend_vs_previous_30_days),
        )

        add_separator()
        rows_added = 0
        add_row(
            "avg_per_day_last_12_months",
            Constants.PERIOD_AVG_LAST_12_MONTHS,
            fmt(stats.avg_per_day_last_12_months, is_avg=True),
        )
        add_row(
            "avg_per_day_this_year",
            Constants.PERIOD_AVG_THIS_YEAR,
            fmt(stats.avg_per_day_this_year, is_avg=True),
        )
        add_row(
            "avg_per_day_last_year",
            Constants.PERIOD_AVG_LAST_YEAR,
            fmt(stats.avg_per_day_last_year, is_avg=True),
        )

        # Yearly totals (dynamic based on show_years)
        add_separator()
        rows_added = 0

        # Create YoY lookup
        yoy_by_year: dict[int, float | None] = {}
        for year, pct in stats.yoy_percentages:
            yoy_by_year[year] = pct

        show_all_yoy = display_config.show_all_yoy if display_config else False

        for idx, (year, total) in enumerate(stats.yearly_totals):
            # Generate row key based on position (for backward compatibility)
            if idx == 0:
                key = "total_this_year"
            elif idx == 1:
                key = "total_last_year"
            elif idx == 2:
                key = "total_year_before"
            else:
                key = f"total_year_{year}"

            # Always use just the year as the label
            label = str(year)

            add_row(key, label, fmt(total))

            # Add YoY row after this year if requested and available
            if year in yoy_by_year:
                prev_year = stats.yearly_totals[idx + 1][0] if idx + 1 < len(stats.yearly_totals) else year - 1

                # Check if we should show this YoY row
                should_show_yoy = show_all_yoy
                if idx == 0:
                    should_show_yoy = should_show_yoy or "yoy_this_vs_last" in show_rows
                elif idx == 1:
                    should_show_yoy = should_show_yoy or "yoy_last_vs_year_before" in show_rows
                else:
                    should_show_yoy = should_show_yoy or f"yoy_{year}" in show_rows

                if should_show_yoy:
                    # Use predefined label for first two YoY rows
                    if idx == 0:
                        yoy_label = Constants.PERIOD_YOY_THIS_VS_LAST
                    elif idx == 1:
                        yoy_label = Constants.PERIOD_YOY_LAST_VS_YEAR_BEFORE
                    else:
                        yoy_label = f"vs {prev_year}"

                    table.add_row(yoy_label, fmt_trend(yoy_by_year[year]))
                    rows_added += 1

        # Standard periods
        add_separator()
        rows_added = 0
        add_row("this_week", Constants.PERIOD_THIS_WEEK, fmt(stats.this_week))
        add_row("this_month", Constants.PERIOD_THIS_MONTH, fmt(stats.this_month))
        add_row("last_month", Constants.PERIOD_LAST_MONTH, fmt(stats.last_month))
        add_row("last_12_months", Constants.PERIOD_LAST_12_MONTHS, fmt(stats.last_12_months))
        add_row("total", Constants.PERIOD_TOTAL, fmt(stats.total))

        self._console.print()
        self._console.print(table)
