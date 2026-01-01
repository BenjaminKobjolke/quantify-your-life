"""Scans directories to find git repositories."""

from pathlib import Path


class RepoScanner:
    """Discovers git repositories in configured root directories."""

    def __init__(self, root_paths: list[str]) -> None:
        """Initialize scanner with root paths to search.

        Args:
            root_paths: List of directory paths that contain git repos.
        """
        self._root_paths = root_paths

    def find_repos(self) -> list[Path]:
        """Find all directories containing a .git folder.

        Only searches one level deep (direct children of root paths).

        Returns:
            List of paths to git repositories.
        """
        repos: list[Path] = []
        for root in self._root_paths:
            root_path = Path(root)
            if not root_path.exists() or not root_path.is_dir():
                continue
            for path in root_path.iterdir():
                if path.is_dir() and (path / ".git").exists():
                    repos.append(path)
        return repos
