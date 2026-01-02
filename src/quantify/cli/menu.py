"""Interactive CLI menu using questionary."""

from datetime import date, timedelta
from typing import cast

import questionary
from rich.console import Console
from rich.table import Table

from quantify.config.constants import Constants
from quantify.services.stats_calculator import TimeStats
from quantify.sources.base import DataSource, SelectableItem
from quantify.sources.git_stats import GitStatsSource
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


def format_lines(value: float, is_avg: bool = False) -> str:
    """Format line count with thousands separator.

    Args:
        value: Number of lines.
        is_avg: If True, show 1 decimal place for averages.

    Returns:
        Formatted string like "1,234 lines" or "0.9 lines".
    """
    if is_avg:
        return f"{value:,.1f} lines"
    return f"{int(value):,} lines"


def format_commits(value: float, is_avg: bool = False) -> str:
    """Format commit count.

    Args:
        value: Number of commits.
        is_avg: If True, show 1 decimal place for averages.

    Returns:
        Formatted string like "1,234 commits" or "0.9 commits".
    """
    if is_avg:
        return f"{value:,.1f} commits"
    count = int(value)
    suffix = "commit" if count == 1 else "commits"
    return f"{count:,} {suffix}"


def format_projects(value: float, is_avg: bool = False) -> str:
    """Format project count.

    Args:
        value: Number of projects.
        is_avg: If True, show 1 decimal place for averages.

    Returns:
        Formatted string like "15 projects" or "1.5 projects".
    """
    if is_avg:
        return f"{value:,.1f} projects"
    count = int(value)
    suffix = "project" if count == 1 else "projects"
    return f"{count:,} {suffix}"


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

        # Main menu loop - back from handlers returns here
        while True:
            # Select source (auto-select if only one)
            source = self._select_source(sources)
            if source is None:
                return  # Exit only when user cancels source selection

            # Handle source-specific flow
            if isinstance(source, TrackAndGraphSource):
                self._handle_track_and_graph(source)
            elif isinstance(source, HometrainerSource):
                self._handle_hometrainer(source)
            elif isinstance(source, GitStatsSource):
                self._handle_git_stats(source)
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

        choices = [
            questionary.Choice(title=s.info.display_name, value=s) for s in sources
        ]
        choices.append(questionary.Choice(title=Constants.MENU_EXIT, value=None))

        result = questionary.select(
            Constants.SOURCE_SELECT_TITLE,
            choices=choices,
        ).ask()

        return cast(DataSource | None, result)

    def _handle_track_and_graph(self, source: TrackAndGraphSource) -> None:
        """Handle Track & Graph source flow."""
        while True:
            view_choice = self._ask_view_type()
            if view_choice is None or view_choice == Constants.MENU_BACK:
                return

            if view_choice == Constants.MENU_GROUP:
                items = source.get_groups()
                if not items:
                    self._console.print(f"[red]{Constants.ERROR_NO_GROUPS}[/red]")
                    continue

                selected = self._select_item_with_back(items, Constants.MENU_SELECT_GROUP)
                if selected is None:
                    continue

                stats = source.get_stats(selected.id, "group")
                self._display_stats(selected.name, stats, source.info.unit, source.info.unit_label)
            else:
                items = source.get_features()
                if not items:
                    self._console.print(f"[red]{Constants.ERROR_NO_FEATURES}[/red]")
                    continue

                selected = self._select_item_with_back(items, Constants.MENU_SELECT_FEATURE)
                if selected is None:
                    continue

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

        # Standard periods
        table.add_row("", "")  # Empty row as separator
        table.add_row(Constants.PERIOD_THIS_WEEK, fmt(stats.this_week))
        table.add_row(Constants.PERIOD_THIS_MONTH, fmt(stats.this_month))
        table.add_row(Constants.PERIOD_LAST_MONTH, fmt(stats.last_month))
        table.add_row(Constants.PERIOD_LAST_12_MONTHS, fmt(stats.last_12_months))
        table.add_row(Constants.PERIOD_TOTAL, fmt(stats.total))

        self._console.print()
        self._console.print(table)

    def _handle_git_stats(self, source: GitStatsSource) -> None:
        """Handle Git Stats source flow with main menu."""
        while True:
            # Main menu for Git Stats
            main_choice = questionary.select(
                "Git Stats - What would you like to do?",
                choices=[
                    Constants.MENU_VIEW_STATS,
                    Constants.MENU_TOP_REPOS,
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
            elif main_choice == Constants.MENU_DATABASE:
                self._manage_database(source)
            elif main_choice == Constants.MENU_DEBUG_GIT:
                self._debug_git_exclusions(source)

    def _view_git_stats(self, source: GitStatsSource) -> None:
        """View git statistics."""
        items = source.get_selectable_items()
        selected = self._select_item_with_back(items, "Select stat type:")
        if selected is None or not isinstance(selected, SelectableItem):
            return

        stats = source.get_stats(selected.id, selected.item_type)

        # Determine unit based on stat type
        if selected.item_type == source.STAT_COMMITS:
            unit = "commits"
            unit_label = "commits"
        elif selected.item_type == source.STAT_PROJECTS_CREATED:
            unit = "projects"
            unit_label = "projects"
        else:
            unit = source.info.unit
            unit_label = source.info.unit_label

        self._display_stats(selected.name, stats, unit, unit_label)

    def _show_top_repos(self, source: GitStatsSource) -> None:
        """Show top 10 repos by net lines changed."""
        # Ask for time period
        period = questionary.select(
            Constants.GIT_SELECT_PERIOD,
            choices=[
                Constants.GIT_PERIOD_LAST_7_DAYS,
                Constants.GIT_PERIOD_LAST_30_DAYS,
                Constants.GIT_PERIOD_LAST_12_MONTHS,
                Constants.GIT_PERIOD_ALL_TIME,
                Constants.MENU_BACK,
            ],
        ).ask()

        if period is None or period == Constants.MENU_BACK:
            return

        # Calculate date range
        today = date.today()
        start_date: date | None = None

        if period == Constants.GIT_PERIOD_LAST_7_DAYS:
            start_date = today - timedelta(days=6)
        elif period == Constants.GIT_PERIOD_LAST_30_DAYS:
            start_date = today - timedelta(days=29)
        elif period == Constants.GIT_PERIOD_LAST_12_MONTHS:
            start_date = today - timedelta(days=364)
        # All time: start_date remains None

        # Get top repos
        top_repos = source.get_top_repos(start_date, today)

        if not top_repos:
            self._console.print("[yellow]No repositories found[/yellow]")
            return

        # Display results
        table = Table(title=f"Top 10 Repos ({period})")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Repository", style="green")
        table.add_column("Net Lines", style="magenta", justify="right")

        for idx, (repo_path, net_lines) in enumerate(top_repos, 1):
            sign = "+" if net_lines >= 0 else ""
            table.add_row(str(idx), repo_path.name, f"{sign}{net_lines:,}")

        self._console.print()
        self._console.print(table)

    def _debug_git_exclusions(self, source: GitStatsSource) -> None:
        """Debug which files are excluded from a repository."""
        repos = source.get_repos()

        if not repos:
            self._console.print("[yellow]No repositories found[/yellow]")
            return

        # Select a repository
        choices = [
            questionary.Choice(title=repo.name, value=repo) for repo in repos
        ]
        choices.append(questionary.Choice(title=Constants.MENU_BACK, value=None))
        selected_repo = questionary.select(
            Constants.DEBUG_SELECT_REPO,
            choices=choices,
        ).ask()

        if selected_repo is None:
            return

        # Analyze exclusions
        analysis = source.analyze_exclusions(selected_repo)
        self._show_exclusion_report(selected_repo.name, analysis)

    def _show_exclusion_report(self, repo_name: str, analysis: dict) -> None:
        """Display exclusion analysis report."""
        table = Table(title=f"{Constants.DEBUG_REPORT_TITLE}: {repo_name}")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="magenta", justify="right")
        table.add_column("Examples", style="dim")

        # Total tracked files
        table.add_row(
            Constants.DEBUG_TOTAL_TRACKED,
            str(analysis["total_tracked"]),
            "",
        )

        # Excluded by directory
        dir_data = analysis["excluded_by_dir"]
        examples = ", ".join(dir_data["examples"][:3]) if dir_data["examples"] else "(none)"
        table.add_row(
            Constants.DEBUG_EXCLUDED_DIR,
            str(dir_data["count"]),
            examples,
        )

        # Excluded by extension
        ext_data = analysis["excluded_by_extension"]
        examples = ", ".join(ext_data["examples"][:3]) if ext_data["examples"] else "(none)"
        table.add_row(
            Constants.DEBUG_EXCLUDED_EXT,
            str(ext_data["count"]),
            examples,
        )

        # Excluded by filename
        name_data = analysis["excluded_by_filename"]
        examples = ", ".join(name_data["examples"][:3]) if name_data["examples"] else "(none)"
        table.add_row(
            Constants.DEBUG_EXCLUDED_NAME,
            str(name_data["count"]),
            examples,
        )

        # Separator
        table.add_row("", "", "")

        # Included files
        inc_data = analysis["included_files"]
        examples = ", ".join(inc_data["examples"][:3]) if inc_data["examples"] else "(none)"
        table.add_row(
            Constants.DEBUG_INCLUDED,
            str(inc_data["count"]),
            examples,
        )

        self._console.print()
        self._console.print(table)
