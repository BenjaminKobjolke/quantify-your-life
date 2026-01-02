"""Project type management handler for git stats."""

from pathlib import Path

import questionary
from rich.console import Console
from rich.table import Table

from quantify.cli.handlers.repo_selector import select_repo
from quantify.config.constants import Constants
from quantify.sources.git_stats import GitStatsSource


class ProjectTypesHandler:
    """Handler for project type management operations."""

    def __init__(self, console: Console) -> None:
        """Initialize handler.

        Args:
            console: Rich console for output.
        """
        self._console = console

    def handle(self, source: GitStatsSource) -> None:
        """Manage project types for repositories."""
        while True:
            choice = questionary.select(
                Constants.PROJECT_TYPE_TITLE,
                choices=[
                    Constants.PROJECT_TYPE_LIST,
                    Constants.PROJECT_TYPE_SET,
                    Constants.PROJECT_TYPE_DETECT,
                    Constants.PROJECT_TYPE_DETECT_ALL,
                    Constants.MENU_BACK,
                ],
            ).ask()

            if choice is None or choice == Constants.MENU_BACK:
                return

            if choice == Constants.PROJECT_TYPE_LIST:
                self._list_project_types(source)
            elif choice == Constants.PROJECT_TYPE_SET:
                self._set_project_type(source)
            elif choice == Constants.PROJECT_TYPE_DETECT:
                self._detect_project_type(source)
            elif choice == Constants.PROJECT_TYPE_DETECT_ALL:
                self._detect_all_project_types(source)

    def prompt_and_set_project_type(
        self,
        source: GitStatsSource,
        repo: Path,
        detection_result: str | None = None,
        allow_skip: bool = False,
    ) -> str | None:
        """Prompt user to select a project type and set it.

        Args:
            source: Git stats source instance.
            repo: Repository path.
            detection_result: "ambiguous", "unknown", or None for manual set.
            allow_skip: If True, show "Skip" option instead of "Back".

        Returns:
            Selected type name, or None if cancelled/skipped.
        """
        # Determine which types to show
        if detection_result == "ambiguous":
            matching = source.get_matching_project_types(repo)
            self._console.print(
                f"[yellow]{Constants.PROJECT_TYPE_AMBIGUOUS}: {', '.join(matching)}[/yellow]"
            )
        elif detection_result == "unknown":
            matching = source.get_available_project_types()
            self._console.print(f"[yellow]No project type detected for {repo.name}[/yellow]")
        else:
            # Manual set - show all types
            matching = source.get_available_project_types()

        # Build choices
        type_choices = [questionary.Choice(title=t, value=t) for t in matching]
        if allow_skip:
            type_choices.append(questionary.Choice(title="Skip (leave unset)", value=None))
        else:
            type_choices.append(questionary.Choice(title=Constants.MENU_BACK, value=None))

        # Prompt user
        selected_type = questionary.select(
            Constants.PROJECT_TYPE_SELECT_TYPE, choices=type_choices
        ).ask()

        # Set and report if selected
        if selected_type:
            source.set_project_type(repo, selected_type, "user")
            msg = Constants.PROJECT_TYPE_SET_SUCCESS.format(repo=repo.name, type=selected_type)
            self._console.print(f"[green]{msg}[/green]")

        return selected_type

    def _list_project_types(self, source: GitStatsSource) -> None:
        """List all stored project types."""
        stored_types = source.get_all_project_types()

        if not stored_types:
            self._console.print(f"[yellow]{Constants.PROJECT_TYPE_NO_STORED}[/yellow]")
            return

        table = Table(title="Stored Project Types")
        table.add_column("Repository", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Source", style="magenta")
        table.add_column("Detected At", style="dim")

        for repo_path, project_type, type_source, detected_at in stored_types:
            repo_name = Path(repo_path).name
            table.add_row(repo_name, project_type, type_source, detected_at)

        self._console.print()
        self._console.print(table)

    def _set_project_type(self, source: GitStatsSource) -> None:
        """Manually set project type for a repository."""
        selected_repo = select_repo(source, self._console)
        if selected_repo is None:
            return

        self.prompt_and_set_project_type(source, selected_repo)

    def _detect_project_type(self, source: GitStatsSource) -> None:
        """Detect and store project type for a single repository."""
        selected_repo = select_repo(source, self._console)
        if selected_repo is None:
            return

        # Detect type
        result = source.detect_and_store_project_type(selected_repo)

        if result in ("ambiguous", "unknown"):
            self.prompt_and_set_project_type(source, selected_repo, result)
        else:
            msg = Constants.PROJECT_TYPE_DETECTED_SUCCESS.format(
                repo=selected_repo.name, type=result
            )
            self._console.print(f"[green]{msg}[/green]")

    def _detect_all_project_types(self, source: GitStatsSource) -> None:
        """Detect project types for all repositories."""
        repos = source.get_repos()
        if not repos:
            self._console.print("[yellow]No repositories found.[/yellow]")
            return

        detected = 0
        needs_input: list[tuple[Path, str]] = []

        # First pass: detect what we can
        for repo in repos:
            result = source.detect_and_store_project_type(repo)
            if result in ("ambiguous", "unknown"):
                needs_input.append((repo, result))
            else:
                detected += 1

        self._console.print(f"[green]Auto-detected {detected} repository types[/green]")

        # Second pass: prompt for repos that need user input
        if needs_input:
            self._console.print(
                f"\n[yellow]{len(needs_input)} repositories need manual type selection:[/yellow]"
            )

            for repo, result in needs_input:
                self._console.print(f"\n[cyan]Repository: {repo.name}[/cyan]")
                self.prompt_and_set_project_type(source, repo, result, allow_skip=True)
