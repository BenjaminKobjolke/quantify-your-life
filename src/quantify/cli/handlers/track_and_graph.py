"""Handler for Track & Graph source."""

from typing import TYPE_CHECKING

import questionary
from rich.console import Console
from rich.table import Table

from quantify.cli.formatting import format_duration
from quantify.cli.handlers.period_selector import (
    get_period_date_range,
    get_period_label,
    select_period,
)
from quantify.config.constants import Constants
from quantify.sources.track_and_graph import TrackAndGraphSource

if TYPE_CHECKING:
    from quantify.cli.menu import Menu


class TrackAndGraphHandler:
    """Handler for Track & Graph source operations."""

    def __init__(self, console: Console, menu: "Menu") -> None:
        """Initialize handler.

        Args:
            console: Rich console for output.
            menu: Parent menu for shared methods like _display_stats.
        """
        self._console = console
        self._menu = menu

    def handle(self, source: TrackAndGraphSource) -> None:
        """Handle Track & Graph source flow with main menu."""
        while True:
            main_choice = questionary.select(
                "Track & Graph - What would you like to do?",
                choices=[
                    Constants.MENU_VIEW_STATS,
                    Constants.MENU_TOP_FEATURES,
                    Constants.MENU_BACK,
                ],
            ).ask()

            if main_choice is None or main_choice == Constants.MENU_BACK:
                break

            if main_choice == Constants.MENU_VIEW_STATS:
                self._view_stats(source)
            elif main_choice == Constants.MENU_TOP_FEATURES:
                self._show_top_features(source)

    def _view_stats(self, source: TrackAndGraphSource) -> None:
        """View statistics for a group or feature."""
        view_choice = self._menu._ask_view_type()
        if view_choice is None or view_choice == Constants.MENU_BACK:
            return

        if view_choice == Constants.MENU_GROUP:
            items = source.get_groups()
            if not items:
                self._console.print(f"[red]{Constants.ERROR_NO_GROUPS}[/red]")
                return

            selected = self._menu._select_item_with_back(items, Constants.MENU_SELECT_GROUP)
            if selected is None:
                return

            stats = source.get_stats(selected.id, "group")
            self._menu._display_stats(
                selected.name, stats, source.info.unit, source.info.unit_label
            )
        else:
            items = source.get_features()
            if not items:
                self._console.print(f"[red]{Constants.ERROR_NO_FEATURES}[/red]")
                return

            selected = self._menu._select_item_with_back(items, Constants.MENU_SELECT_FEATURE)
            if selected is None:
                return

            stats = source.get_stats(selected.id, "feature")
            self._menu._display_stats(
                selected.name, stats, source.info.unit, source.info.unit_label
            )

    def _show_top_features(self, source: TrackAndGraphSource) -> None:
        """Show top 10 features in a selected group."""
        # Select group
        items = source.get_groups()
        if not items:
            self._console.print(f"[red]{Constants.ERROR_NO_GROUPS}[/red]")
            return

        selected = self._menu._select_item_with_back(items, Constants.MENU_SELECT_GROUP)
        if selected is None:
            return

        # Select time period
        period_key = select_period()
        if period_key is None:
            return

        # Get date range for selected period
        start_date, end_date = get_period_date_range(period_key)
        period_label = get_period_label(period_key)

        # Get top features
        top_features = source.get_top_features_in_group(selected.id, start_date, end_date)

        if not top_features:
            self._console.print(f"[yellow]{Constants.TOP_FEATURES_NO_DATA}[/yellow]")
            return

        # Display results
        table = Table(title=f"Top 10 Features in {selected.name} ({period_label})")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Feature", style="green")
        table.add_column("Time", style="magenta", justify="right")

        for idx, (feature_name, value) in enumerate(top_features, 1):
            formatted_value = format_duration(value)
            table.add_row(str(idx), feature_name, formatted_value)

        self._console.print()
        self._console.print(table)


def handle_track_and_graph(console: Console, source: TrackAndGraphSource, menu: "Menu") -> None:
    """Handle Track & Graph source flow (legacy wrapper).

    Args:
        console: Rich console for output.
        source: Track & Graph data source.
        menu: Parent menu for shared methods.
    """
    handler = TrackAndGraphHandler(console, menu)
    handler.handle(source)
