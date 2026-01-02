"""Project type detection for git repositories.

Detects project types (Unity, Flutter, Python, etc.) based on
presence of marker files and directories.
"""

import fnmatch
import logging
from pathlib import Path

from quantify.config.settings import DEFAULT_PROJECT_TYPES, ProjectTypeConfig

logger = logging.getLogger(__name__)


def get_matching_types(repo_path: Path) -> list[str]:
    """Get all project types that match the repository.

    Args:
        repo_path: Path to the git repository root.

    Returns:
        List of matching project type names (e.g., ["unity", "node"]).
        Empty list if only "generic" matches.
    """
    matches: list[str] = []

    for type_name, config in DEFAULT_PROJECT_TYPES.items():
        if type_name == "generic":
            continue  # Generic always matches, skip for now

        if _matches_project_type(repo_path, config):
            matches.append(type_name)

    return matches


def detect_project_type(repo_path: Path) -> str | None:
    """Detect the project type for a repository.

    Args:
        repo_path: Path to the git repository root.

    Returns:
        Project type name if exactly one match found.
        None if no matches or multiple matches (user must choose).
    """
    matches = get_matching_types(repo_path)

    if len(matches) == 1:
        logger.debug(f"Detected project type '{matches[0]}' for {repo_path}")
        return matches[0]
    elif len(matches) == 0:
        logger.debug(f"No specific project type detected for {repo_path}")
        return None  # No match, user must choose
    else:
        logger.debug(f"Multiple project types match {repo_path}: {matches}")
        return None  # Ambiguous, user must choose


def get_project_type_config(type_name: str) -> ProjectTypeConfig:
    """Get the configuration for a project type.

    Args:
        type_name: The project type name (e.g., "unity", "flutter").

    Returns:
        ProjectTypeConfig for the type, or generic if not found.
    """
    return DEFAULT_PROJECT_TYPES.get(type_name, DEFAULT_PROJECT_TYPES["generic"])


def _matches_project_type(repo_path: Path, config: ProjectTypeConfig) -> bool:
    """Check if a repository matches a project type configuration.

    A project type matches if:
    - At least one detection_file exists (supports glob patterns), OR
    - All detection_dirs exist (if any are specified)

    Args:
        repo_path: Path to the git repository root.
        config: Project type configuration to check.

    Returns:
        True if the repository matches the project type.
    """
    # Check for detection files (any match counts)
    for pattern in config.detection_files:
        if _has_matching_file(repo_path, pattern):
            return True

    # Check for detection directories (all must exist)
    if config.detection_dirs:
        all_dirs_exist = all(
            (repo_path / dir_name).is_dir() for dir_name in config.detection_dirs
        )
        if all_dirs_exist:
            return True

    return False


def _has_matching_file(repo_path: Path, pattern: str) -> bool:
    """Check if any file in repo root matches the pattern.

    Args:
        repo_path: Path to the git repository root.
        pattern: Filename or glob pattern (e.g., "*.sln", "pubspec.yaml").

    Returns:
        True if at least one matching file exists.
    """
    if "*" in pattern:
        # Glob pattern - check root directory only
        for path in repo_path.iterdir():
            if path.is_file() and fnmatch.fnmatch(path.name, pattern):
                return True
        return False
    else:
        # Exact filename
        return (repo_path / pattern).is_file()
