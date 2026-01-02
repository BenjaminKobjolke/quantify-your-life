"""Main handler for Git Stats source."""

from datetime import date
from typing import TYPE_CHECKING

import questionary
from rich.console import Console
from rich.table import Table

from quantify.cli.formatting import format_commits, format_lines, format_projects
from quantify.cli.handlers.database import DatabaseHandler
from quantify.cli.handlers.debug import DebugHandler
from quantify.cli.handlers.period_selector import (
    get_period_date_range,
    get_period_label,
    get_stat_value_for_period,
    select_period,
)
from quantify.cli.handlers.project_types import ProjectTypesHandler
from quantify.config.constants import Constants
from quantify.sources.git_stats import GitStatsSource

if TYPE_CHECKING:
    from quantify.cli.menu import Menu


class GitStatsHandler:
    """Handler for Git Stats source operations."""

    def __init__(self, console: Console, menu: "Menu") -> None:
        """Initialize handler.

        Args:
            console: Rich console for output.
            menu: Parent menu for shared methods like _display_stats.
        """
        self._console = console
        self._menu = menu

        # Initialize sub-handlers
        self._project_types = ProjectTypesHandler(console)
        self._database = DatabaseHandler(console)
        self._debug = DebugHandler(console, self._project_types)

    def handle(self, source: GitStatsSource) -> None:
        """Handle Git Stats source flow with main menu."""
        while True:
            main_choice = questionary.select(
                "Git Stats - What would you like to do?",
                choices=[
                    Constants.MENU_VIEW_STATS,
                    Constants.MENU_TOP_REPOS,
                    Constants.MENU_PROJECT_TYPES,
                    Constants.MENU_DATABASE,
                    Constants.MENU_DEBUG_GIT,
                    Constants.MENU_BACK,
                ],
            ).ask()

            if main_choice is None or main_choice == Constants.MENU_BACK:
                break

            if main_choice == Constants.MENU_VIEW_STATS:
                self._view_git_stats(source)
            elif main_choice == Constants.MENU_TOP_REPOS:
                self._show_top_repos(source)
            elif main_choice == Constants.MENU_PROJECT_TYPES:
                self._project_types.handle(source)
            elif main_choice == Constants.MENU_DATABASE:
                self._database.handle(source)
            elif main_choice == Constants.MENU_DEBUG_GIT:
                self._debug.debug_git_exclusions(source)

    def _view_git_stats(self, source: GitStatsSource) -> None:
        """View git statistics."""
        items = source.get_selectable_items()
        selected = self._menu._select_item_with_back(items, "Select stat type:")
        if selected is None:
            return

        # Select time period
        period_key = select_period()
        if period_key is None:
            return

        # Get stats
        stats = source.get_stats(selected.id, selected.item_type)

        # Get value for selected period
        value = get_stat_value_for_period(stats, period_key)
        period_label = get_period_label(period_key)

        # Format value based on stat type
        if selected.item_type == source.STAT_COMMITS:
            formatted = format_commits(value)
        elif selected.item_type == source.STAT_PROJECTS_CREATED:
            formatted = format_projects(value)
        else:
            formatted = format_lines(value)

        # Display result
        self._console.print()
        self._console.print(
            f"[cyan]{selected.name}[/cyan] - [yellow]{period_label}[/yellow]: "
            f"[green]{formatted}[/green]"
        )

        # Offer details for commits and projects created (if count > 0)
        if value > 0 and selected.item_type in (
            source.STAT_COMMITS,
            source.STAT_PROJECTS_CREATED,
        ):
            self._console.print()
            if questionary.confirm(Constants.GIT_SHOW_DETAILS).ask():
                start_date, end_date = get_period_date_range(period_key)
                self._show_stat_details(
                    source, selected.item_type, start_date, end_date, period_label
                )

    def _show_top_repos(self, source: GitStatsSource) -> None:
        """Show top 10 repos by net lines changed."""
        period_key = select_period()
        if period_key is None:
            return

        # Get date range for selected period
        start_date, end_date = get_period_date_range(period_key)
        period_label = get_period_label(period_key)

        # Get top repos
        top_repos = source.get_top_repos(start_date, end_date)

        if not top_repos:
            self._console.print("[yellow]No repositories found[/yellow]")
            return

        # Display results
        table = Table(title=f"Top 10 Repos ({period_label})")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Repository", style="green")
        table.add_column("Net Lines", style="magenta", justify="right")

        for idx, (repo_path, net_lines) in enumerate(top_repos, 1):
            sign = "+" if net_lines >= 0 else ""
            table.add_row(str(idx), repo_path.name, f"{sign}{net_lines:,}")

        self._console.print()
        self._console.print(table)

    def _show_stat_details(
        self,
        source: GitStatsSource,
        stat_type: str,
        start_date: date | None,
        end_date: date,
        period_label: str,
    ) -> None:
        """Show detailed breakdown for a stat type.

        Args:
            source: Git stats source.
            stat_type: The stat type (commits or projects_created).
            start_date: Period start date.
            end_date: Period end date.
            period_label: Human-readable period label for title.
        """
        if stat_type == source.STAT_PROJECTS_CREATED:
            self._show_projects_created_details(
                source, start_date, end_date, period_label
            )
        elif stat_type == source.STAT_COMMITS:
            self._show_commits_details(source, start_date, end_date, period_label)

    def _show_projects_created_details(
        self,
        source: GitStatsSource,
        start_date: date | None,
        end_date: date,
        period_label: str,
    ) -> None:
        """Show list of projects created in the period.

        Args:
            source: Git stats source.
            start_date: Period start date.
            end_date: Period end date.
            period_label: Human-readable period label for title.
        """
        projects = source.get_projects_created_in_period(start_date, end_date)

        if not projects:
            self._console.print(f"[yellow]{Constants.GIT_NO_PROJECTS_FOUND}[/yellow]")
            return

        table = Table(title=f"Projects Created ({period_label})")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Repository", style="green")
        table.add_column("Created", style="magenta", justify="right")

        for idx, (repo_path, creation_date) in enumerate(projects, 1):
            table.add_row(str(idx), repo_path.name, creation_date.isoformat())

        self._console.print()
        self._console.print(table)

    def _show_commits_details(
        self,
        source: GitStatsSource,
        start_date: date | None,
        end_date: date,
        period_label: str,
    ) -> None:
        """Show commit counts by repository for the period.

        Args:
            source: Git stats source.
            start_date: Period start date.
            end_date: Period end date.
            period_label: Human-readable period label for title.
        """
        commits_by_repo = source.get_commits_by_repo_in_period(start_date, end_date)

        if not commits_by_repo:
            self._console.print(f"[yellow]{Constants.GIT_NO_COMMITS_FOUND}[/yellow]")
            return

        table = Table(title=f"Commits by Repository ({period_label})")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Repository", style="green")
        table.add_column("Commits", style="magenta", justify="right")

        for idx, (repo_path, commit_count) in enumerate(commits_by_repo, 1):
            table.add_row(str(idx), repo_path.name, f"{commit_count:,}")

        self._console.print()
        self._console.print(table)
