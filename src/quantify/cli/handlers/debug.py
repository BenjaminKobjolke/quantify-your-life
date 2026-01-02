"""Debug and exclusion analysis handler for git stats."""

from typing import TYPE_CHECKING

import questionary
from rich.console import Console
from rich.table import Table

from quantify.cli.utils import export_exclusion_log, open_file
from quantify.config.constants import Constants
from quantify.sources.git_stats import GitStatsSource

if TYPE_CHECKING:
    from quantify.cli.handlers.project_types import ProjectTypesHandler


class DebugHandler:
    """Handler for debug and exclusion analysis operations."""

    def __init__(self, console: Console, project_types_handler: "ProjectTypesHandler") -> None:
        """Initialize handler.

        Args:
            console: Rich console for output.
            project_types_handler: Handler for project type prompting.
        """
        self._console = console
        self._project_types = project_types_handler

    def debug_git_exclusions(self, source: GitStatsSource) -> None:
        """Debug which files are excluded from a repository."""
        repos = source.get_repos()

        if not repos:
            self._console.print("[yellow]No repositories found[/yellow]")
            return

        # Select a repository
        choices = [questionary.Choice(title=repo.name, value=repo) for repo in repos]
        choices.append(questionary.Choice(title=Constants.MENU_BACK, value=None))
        selected_repo = questionary.select(
            Constants.DEBUG_SELECT_REPO,
            choices=choices,
        ).ask()

        if selected_repo is None:
            return

        # Check if project type is set, prompt if not
        stored = source.get_project_type(selected_repo)
        if not stored:
            result = source.detect_and_store_project_type(selected_repo)
            if result in ("ambiguous", "unknown"):
                selected = self._project_types.prompt_and_set_project_type(
                    source, selected_repo, result
                )
                if not selected:
                    # User cancelled, use generic
                    source.set_project_type(selected_repo, "generic", "user")
                    self._console.print("[dim]Using generic project type[/dim]")

        # Analyze exclusions using project type
        analysis = source.analyze_exclusions_for_repo(selected_repo)
        self._show_exclusion_report(selected_repo.name, analysis)

        # Export log file
        log_path = export_exclusion_log(selected_repo, analysis, self._console)
        self._console.print(f"\n[cyan]{Constants.DEBUG_LOG_EXPORTED.format(path=log_path)}[/cyan]")

        # Offer to open log file
        if questionary.confirm(Constants.DEBUG_OPEN_LOG).ask():
            open_file(log_path, self._console)

    def _show_exclusion_report(self, repo_name: str, analysis: dict[str, object]) -> None:
        """Display exclusion analysis report."""
        table = Table(title=f"{Constants.DEBUG_REPORT_TITLE}: {repo_name}")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="magenta", justify="right")
        table.add_column("Examples", style="dim")

        # Project type (if available)
        project_type = analysis.get("project_type")
        if project_type:
            table.add_row(
                Constants.DEBUG_PROJECT_TYPE,
                "",
                f"[green]{project_type}[/green]",
            )
            table.add_row("", "", "")

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

        # Excluded by include pattern (project-type-specific)
        pattern_data = analysis.get("excluded_by_include_pattern", {"count": 0, "examples": []})
        if pattern_data["count"] > 0:
            pattern_examples = pattern_data["examples"][:3]
            examples = ", ".join(pattern_examples) if pattern_examples else "(none)"
            table.add_row(
                Constants.DEBUG_EXCLUDED_PATTERN,
                str(pattern_data["count"]),
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
