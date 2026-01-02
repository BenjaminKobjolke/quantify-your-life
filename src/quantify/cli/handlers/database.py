"""Database and cache management handler for git stats."""

import questionary
from rich.console import Console

from quantify.cli.handlers.repo_selector import select_repo
from quantify.config.constants import Constants
from quantify.sources.git_stats import GitStatsSource


class DatabaseHandler:
    """Handler for database and cache management operations."""

    def __init__(self, console: Console) -> None:
        """Initialize handler.

        Args:
            console: Rich console for output.
        """
        self._console = console

    def handle(self, source: GitStatsSource) -> None:
        """Manage git stats database."""
        while True:
            choice = questionary.select(
                "Database - What would you like to do?",
                choices=["Clear cache for a repository", Constants.MENU_BACK],
            ).ask()
            if choice is None or choice == Constants.MENU_BACK:
                return
            if choice == "Clear cache for a repository":
                self._clear_repo_cache(source)

    def _clear_repo_cache(self, source: GitStatsSource) -> None:
        """Clear cache for a selected repository."""
        selected = select_repo(source, self._console, "Select repository to clear:")
        if selected is None:
            return

        if questionary.confirm(f"Clear cache for '{selected.name}'?").ask():
            source.clear_repo_cache(selected)
            self._console.print(f"[green]Cache cleared for {selected.name}[/green]")
