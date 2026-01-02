"""Handler for Track & Graph source."""

from typing import TYPE_CHECKING

from rich.console import Console

from quantify.config.constants import Constants
from quantify.sources.track_and_graph import TrackAndGraphSource

if TYPE_CHECKING:
    from quantify.cli.menu import Menu


def handle_track_and_graph(console: Console, source: TrackAndGraphSource, menu: "Menu") -> None:
    """Handle Track & Graph source flow.

    Args:
        console: Rich console for output.
        source: Track & Graph data source.
        menu: Parent menu for shared methods.
    """
    while True:
        view_choice = menu._ask_view_type()
        if view_choice is None or view_choice == Constants.MENU_BACK:
            return

        if view_choice == Constants.MENU_GROUP:
            items = source.get_groups()
            if not items:
                console.print(f"[red]{Constants.ERROR_NO_GROUPS}[/red]")
                continue

            selected = menu._select_item_with_back(items, Constants.MENU_SELECT_GROUP)
            if selected is None:
                continue

            stats = source.get_stats(selected.id, "group")
            menu._display_stats(selected.name, stats, source.info.unit, source.info.unit_label)
        else:
            items = source.get_features()
            if not items:
                console.print(f"[red]{Constants.ERROR_NO_FEATURES}[/red]")
                continue

            selected = menu._select_item_with_back(items, Constants.MENU_SELECT_FEATURE)
            if selected is None:
                continue

            stats = source.get_stats(selected.id, "feature")
            menu._display_stats(selected.name, stats, source.info.unit, source.info.unit_label)
