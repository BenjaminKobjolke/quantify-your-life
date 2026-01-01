"""Parses git log output to extract line statistics."""

import logging
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GitStats:
    """Statistics from git log for a date range."""

    added: int
    removed: int

    @property
    def net(self) -> int:
        """Net lines (added - removed)."""
        return self.added - self.removed


class GitLogParser:
    """Runs git log and parses numstat output."""

    def __init__(
        self,
        author: str,
        exclude_dirs: list[str],
        exclude_extensions: list[str],
        exclude_filenames: list[str],
    ) -> None:
        """Initialize parser with filtering options.

        Args:
            author: Git author name to filter commits.
            exclude_dirs: Directory names to exclude.
            exclude_extensions: File extensions to exclude.
            exclude_filenames: Specific filenames to exclude.
        """
        self._author = author
        self._exclude_dirs = set(exclude_dirs)
        self._exclude_extensions = set(exclude_extensions)
        self._exclude_filenames = set(exclude_filenames)
        self._failed_repos: set[Path] = set()  # Cache repos that failed

    def get_stats(
        self,
        repo_path: Path,
        start_date: date | None,
        end_date: date | None,
    ) -> GitStats:
        """Get line statistics for a repository in a date range.

        Args:
            repo_path: Path to the git repository.
            start_date: First day to include (None for no lower bound).
            end_date: Last day to include (None for today).

        Returns:
            GitStats with added and removed line counts.
        """
        # Skip repos that previously failed (e.g., no commits)
        if repo_path in self._failed_repos:
            return GitStats(added=0, removed=0)

        try:
            output = self._run_git_log(repo_path, start_date, end_date)
            return self._parse_numstat(output)
        except subprocess.CalledProcessError as e:
            stderr_msg = e.stderr.strip() if e.stderr else "unknown error"
            logger.warning(f"Git error in {repo_path.name}: {stderr_msg}")
            self._failed_repos.add(repo_path)
            return GitStats(added=0, removed=0)
        except subprocess.SubprocessError as e:
            logger.warning(f"Failed to get git stats for {repo_path}: {e}")
            self._failed_repos.add(repo_path)
            return GitStats(added=0, removed=0)
        except FileNotFoundError:
            logger.warning("Git is not installed or not in PATH")
            return GitStats(added=0, removed=0)

    def _run_git_log(
        self,
        repo_path: Path,
        start_date: date | None,
        end_date: date | None,
    ) -> str:
        """Run git log command and return output.

        Args:
            repo_path: Path to the git repository.
            start_date: First day to include.
            end_date: Last day to include.

        Returns:
            Raw output from git log --numstat.
        """
        cmd = [
            "git",
            "-C",
            str(repo_path),
            "log",
            f"--author={self._author}",
            "--pretty=tformat:",
            "--numstat",
        ]

        if start_date:
            # Include start of day to make boundary inclusive
            cmd.append(f"--since={start_date.isoformat()} 00:00:00")
        if end_date:
            # Include end of day to make boundary inclusive
            cmd.append(f"--until={end_date.isoformat()} 23:59:59")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
        return result.stdout

    def _parse_numstat(self, output: str) -> GitStats:
        """Parse git numstat output into GitStats.

        Format: added<tab>removed<tab>filepath
        Binary files show "-" for added/removed.

        Args:
            output: Raw git log --numstat output.

        Returns:
            GitStats with aggregated line counts.
        """
        total_added = 0
        total_removed = 0

        for line in output.strip().split("\n"):
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) != 3:
                continue

            added_str, removed_str, filepath = parts

            # Skip binary files (shown as "-")
            if added_str == "-" or removed_str == "-":
                continue

            # Apply exclusion filters
            if self._should_exclude(filepath):
                continue

            try:
                total_added += int(added_str)
                total_removed += int(removed_str)
            except ValueError:
                # Skip lines with non-numeric values
                continue

        return GitStats(added=total_added, removed=total_removed)

    def _should_exclude(self, filepath: str) -> bool:
        """Check if a file should be excluded based on filters.

        Args:
            filepath: Path to the file (relative to repo root).

        Returns:
            True if the file should be excluded.
        """
        path = Path(filepath)

        # Check if any path component is in excluded dirs
        for part in path.parts:
            if part in self._exclude_dirs:
                return True

        # Check filename
        if path.name in self._exclude_filenames:
            return True

        # Check extension (handle multi-part extensions like .g.dart)
        name = path.name
        return any(name.endswith(ext) for ext in self._exclude_extensions)

    def get_daily_stats(self, repo_path: Path, day: date) -> GitStats:
        """Get stats for a single day.

        Convenience method that wraps get_stats for single-day queries.
        This is used by the cache to fetch missing individual days.

        Args:
            repo_path: Path to the git repository.
            day: The specific date to query.

        Returns:
            GitStats with added and removed line counts for that day.
        """
        return self.get_stats(repo_path, start_date=day, end_date=day)
