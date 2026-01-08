"""Project selection UI component."""

from typing import cast

import questionary
from rich.console import Console

from quantify.config.constants import Constants
from quantify.config.project_manager import ProjectManager


class ProjectSelector:
    """Interactive project selection component."""

    def __init__(self, project_manager: ProjectManager) -> None:
        """Initialize selector.

        Args:
            project_manager: ProjectManager instance for project discovery.
        """
        self._pm = project_manager
        self._console = Console()

    def select(self) -> str | None:
        """Prompt user to select a project.

        Returns:
            - Project name (str) if a project was selected
            - Empty string ("") if user chose to use legacy config
            - None if user chose to exit or cancelled
        """
        projects = self._pm.discover_projects()

        choices: list[questionary.Choice] = []

        # Add existing projects
        for proj in projects:
            status = "" if proj.has_config else Constants.PROJECT_NO_CONFIG_SUFFIX
            choices.append(
                questionary.Choice(
                    title=f"{proj.name}{status}",
                    value=proj.name,
                )
            )

        # Add "Create new project" option
        choices.append(
            questionary.Choice(
                title=Constants.PROJECT_CREATE_NEW,
                value="__create__",
            )
        )

        # Add "Use root config.json" option if legacy config exists
        if self._pm.has_legacy_config():
            choices.append(
                questionary.Choice(
                    title=Constants.PROJECT_USE_LEGACY,
                    value="",
                )
            )

        # Add Exit option
        choices.append(
            questionary.Choice(
                title=Constants.MENU_EXIT,
                value=None,
            )
        )

        result = questionary.select(
            Constants.PROJECT_SELECT_TITLE,
            choices=choices,
        ).ask()

        if result == "__create__":
            return self._create_new_project()

        return cast(str | None, result)

    def _create_new_project(self) -> str | None:
        """Prompt user to create a new project.

        Returns:
            Name of the created project, or None if cancelled.
        """
        name = questionary.text(
            Constants.PROJECT_ENTER_NAME,
            validate=lambda x: len(x.strip()) > 0 or "Name cannot be empty",
        ).ask()

        if name is None:
            return None

        # Sanitize name: lowercase, replace spaces with dashes
        name = name.strip().lower().replace(" ", "-")

        # Create project directory
        project_path = self._pm.create_project(name)

        # Create minimal config.json
        config_path = project_path / Constants.CONFIG_FILE_NAME
        if not config_path.exists():
            config_path.write_text(
                '{\n    "export": {\n        "path": "",\n        "entries": []\n    }\n}',
                encoding="utf-8",
            )

        self._console.print(
            Constants.PROJECT_CREATED.format(name=name),
            style="green",
        )

        return cast(str, name)
