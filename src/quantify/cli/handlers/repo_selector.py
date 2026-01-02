"""Repository selection utilities for git stats handlers."""

from pathlib import Path

import questionary
from rich.console import Console

from quantify.config.constants import Constants
from quantify.sources.git_stats import GitStatsSource


def select_repo(
    source: GitStatsSource,
    console: Console,
    prompt: str = Constants.PROJECT_TYPE_SELECT_REPO,
) -> Path | None:
    """Prompt user to select a repository.

    Args:
        source: Git stats source to get repos from.
        console: Console for output messages.
        prompt: Prompt text for selection.

    Returns:
        Selected repository path or None if cancelled/no repos.
    """
    repos = source.get_repos()

    if not repos:
        console.print("[yellow]No repositories found.[/yellow]")
        return None

    choices = [questionary.Choice(title=r.name, value=r) for r in repos]
    choices.append(questionary.Choice(title=Constants.MENU_BACK, value=None))

    return questionary.select(prompt, choices=choices).ask()
