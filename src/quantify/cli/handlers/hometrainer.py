"""Handler for Hometrainer source."""

from typing import TYPE_CHECKING

import questionary
from rich.console import Console

from quantify.config.constants import Constants
from quantify.sources.hometrainer import HometrainerSource

if TYPE_CHECKING:
    from quantify.cli.menu import Menu


def handle_hometrainer(console: Console, source: HometrainerSource, menu: "Menu") -> None:
    """Handle Hometrainer source flow.

    Args:
        console: Rich console for output.
        source: Hometrainer data source.
        menu: Parent menu for shared methods.
    """
    # Hometrainer has single stats, show directly
    items = source.get_selectable_items()
    if items:
        item = items[0]
        stats = source.get_stats(item.id, item.item_type)
        menu._display_stats(item.name, stats, source.info.unit, source.info.unit_label)
        # Wait for user to press back
        questionary.select(
            "Action:",
            choices=[Constants.MENU_BACK],
        ).ask()
