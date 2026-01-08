"""Project discovery and management."""

from dataclasses import dataclass
from pathlib import Path

from quantify.config.constants import Constants


@dataclass(frozen=True)
class ProjectInfo:
    """Information about a discovered project."""

    name: str
    path: Path
    has_config: bool


class ProjectManager:
    """Manages project discovery and creation."""

    PROJECTS_DIR = "projects"

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialize project manager.

        Args:
            base_dir: Base directory to look for projects folder.
                     Defaults to current working directory.
        """
        self._base_dir = base_dir or Path.cwd()
        self._projects_dir = self._base_dir / self.PROJECTS_DIR

    def get_projects_dir(self) -> Path:
        """Get the projects directory path.

        Returns:
            Path to the projects directory.
        """
        return self._projects_dir

    def get_base_dir(self) -> Path:
        """Get the base directory path.

        Returns:
            Path to the base directory.
        """
        return self._base_dir

    def projects_exist(self) -> bool:
        """Check if projects directory exists and has at least one project.

        Returns:
            True if projects directory exists with at least one project.
        """
        if not self._projects_dir.exists():
            return False
        return len(self.discover_projects()) > 0

    def has_legacy_config(self) -> bool:
        """Check if legacy single config.json exists at root.

        Returns:
            True if root config.json exists.
        """
        return (self._base_dir / Constants.CONFIG_FILE_NAME).exists()

    def discover_projects(self) -> list[ProjectInfo]:
        """Discover all available projects.

        Scans the projects/ directory for subdirectories.
        Each subdirectory is considered a project.

        Returns:
            List of ProjectInfo objects for discovered projects.
        """
        projects: list[ProjectInfo] = []

        if not self._projects_dir.exists():
            return projects

        for item in sorted(self._projects_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                config_path = item / Constants.CONFIG_FILE_NAME
                projects.append(
                    ProjectInfo(
                        name=item.name,
                        path=item,
                        has_config=config_path.exists(),
                    )
                )

        return projects

    def get_project_path(self, project_name: str) -> Path:
        """Get path to a specific project directory.

        Args:
            project_name: Name of the project.

        Returns:
            Path to the project directory.
        """
        return self._projects_dir / project_name

    def get_global_config_path(self) -> Path:
        """Get path to global config.json in projects directory.

        Returns:
            Path to projects/config.json.
        """
        return self._projects_dir / Constants.CONFIG_FILE_NAME

    def project_exists(self, project_name: str) -> bool:
        """Check if a project exists.

        Args:
            project_name: Name of the project.

        Returns:
            True if the project directory exists.
        """
        return self.get_project_path(project_name).exists()

    def create_project(self, name: str) -> Path:
        """Create a new project directory.

        Creates projects/ directory if needed.

        Args:
            name: Name of the project to create.

        Returns:
            Path to the created project directory.
        """
        project_path = self._projects_dir / name
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path
