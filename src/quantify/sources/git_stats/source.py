"""Git statistics data source."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from rich.progress import Progress, TaskID

from quantify.config.settings import DEFAULT_PROJECT_TYPES
from quantify.services.stats_calculator import StatsCalculator, TimeStats
from quantify.sources.base import DataProvider, DataSource, SelectableItem, SourceInfo
from quantify.sources.git_stats.data_provider import (
    GitStatsDataProvider,
    ProjectsCreatedDataProvider,
)
from quantify.sources.git_stats.git_log_parser import GitLogParser
from quantify.sources.git_stats.progress import ProgressMixin
from quantify.sources.git_stats.project_type_detector import (
    detect_project_type,
    get_matching_types,
    get_project_type_config,
)
from quantify.sources.git_stats.repo_scanner import RepoScanner
from quantify.sources.git_stats.stats_cache import GitStatsCache


class GitStatsSource(ProgressMixin, DataSource):
    """Data source for git line statistics across repositories."""

    # Stat type constants
    STAT_ADDED = "added"
    STAT_REMOVED = "removed"
    STAT_NET = "net"
    STAT_COMMITS = "commits"
    STAT_PROJECTS_CREATED = "projects_created"

    # Cache location
    CACHE_DIR = Path.home() / ".quantify-your-life"
    CACHE_DB_NAME = "git_stats_cache.db"

    def __init__(
        self,
        author: str,
        root_paths: list[str],
        exclude_dirs: list[str],
        exclude_extensions: list[str],
        exclude_filenames: list[str],
    ) -> None:
        """Initialize git stats source.

        Args:
            author: Git author name to filter commits.
            root_paths: Directories containing git repositories.
            exclude_dirs: Directory names to exclude from stats.
            exclude_extensions: File extensions to exclude from stats.
            exclude_filenames: Specific filenames to exclude from stats.
        """
        self._author = author
        self._root_paths = root_paths
        self._exclude_dirs = exclude_dirs
        self._exclude_extensions = exclude_extensions
        self._exclude_filenames = exclude_filenames
        self._repos: list[Path] | None = None
        self._parser: GitLogParser | None = None  # Default parser (no project type)
        self._parsers: dict[str, GitLogParser] = {}  # Parsers by project type
        self._cache: GitStatsCache | None = None
        self._console = Console()
        self._progress: Progress | None = None
        self._task_id: TaskID | None = None

    @property
    def info(self) -> SourceInfo:
        """Return metadata about this data source."""
        return SourceInfo(
            id="git_stats",
            display_name="Git Stats",
            unit="lines",
            unit_label="lines",
        )

    def is_configured(self) -> bool:
        """Return True if author and at least one root path exist."""
        if not self._author:
            return False
        if not self._root_paths:
            return False
        # Check if at least one root path exists
        return any(Path(p).exists() for p in self._root_paths)

    def get_selectable_items(self) -> list[SelectableItem]:
        """Return stat items for git statistics."""
        return [
            SelectableItem(None, "Git: Lines Added", self.STAT_ADDED),
            SelectableItem(None, "Git: Lines Removed", self.STAT_REMOVED),
            SelectableItem(None, "Git: Net Lines", self.STAT_NET),
            SelectableItem(None, "Git: Commits", self.STAT_COMMITS),
            SelectableItem(None, "Git: Projects Created", self.STAT_PROJECTS_CREATED),
        ]

    def get_item_name(self, item_id: int | None, item_type: str) -> str | None:
        """Get the name of an item by type.

        Args:
            item_id: Not used (always None for git stats).
            item_type: Stat type (added, removed, net, commits, projects_created).

        Returns:
            The item name, or None if not found.
        """
        names = {
            self.STAT_ADDED: "Git: Lines Added",
            self.STAT_REMOVED: "Git: Lines Removed",
            self.STAT_NET: "Git: Net Lines",
            self.STAT_COMMITS: "Git: Commits",
            self.STAT_PROJECTS_CREATED: "Git: Projects Created",
        }
        return names.get(item_type)

    def get_data_provider(
        self, item_id: int | None = None, item_type: str | None = None
    ) -> DataProvider:
        """Get a data provider for the specified stat type.

        Args:
            item_id: Not used (always None for git stats).
            item_type: Stat type (added, removed, net, commits, projects_created).

        Returns:
            Appropriate data provider for the requested stat type.
        """
        self._ensure_initialized()
        stat_type = item_type or self.STAT_NET
        assert self._repos is not None
        assert self._parser is not None
        assert self._cache is not None

        if stat_type == self.STAT_PROJECTS_CREATED:
            return ProjectsCreatedDataProvider(
                self._repos,
                self._parser,
                progress_callback=self._on_progress,
            )

        return GitStatsDataProvider(
            self._repos,
            self._parser,
            stat_type,
            self._cache,
            progress_callback=self._on_progress,
        )

    def get_stats(
        self, item_id: int | None = None, item_type: str | None = None
    ) -> TimeStats:
        """Calculate statistics for the specified stat type.

        Args:
            item_id: Not used (always None for git stats).
            item_type: "added", "removed", or "net".

        Returns:
            TimeStats with all calculated periods.
        """
        provider = self.get_data_provider(item_id, item_type)
        calculator = StatsCalculator()

        # Show progress during calculation (total updated by _on_progress callback)
        with self._progress_context("Scanning repositories..."):
            return calculator.calculate(provider.get_sum)

    def close(self) -> None:
        """Close any resources held by this source."""
        if self._cache is not None:
            self._cache.close()
            self._cache = None

    def _ensure_initialized(self) -> None:
        """Ensure repos, parser, and cache are initialized."""
        if self._repos is None:
            scanner = RepoScanner(self._root_paths)
            self._repos = scanner.find_repos()
        if self._parser is None:
            self._parser = GitLogParser(
                self._author,
                self._exclude_dirs,
                self._exclude_extensions,
                self._exclude_filenames,
            )
        if self._cache is None:
            cache_path = self.CACHE_DIR / self.CACHE_DB_NAME
            self._cache = GitStatsCache(cache_path)

    def get_repos(self) -> list[Path]:
        """Get list of discovered repositories.

        Returns:
            List of repository paths.
        """
        self._ensure_initialized()
        assert self._repos is not None
        return self._repos

    def get_parser(self) -> GitLogParser:
        """Get the git log parser.

        Returns:
            GitLogParser instance.
        """
        self._ensure_initialized()
        assert self._parser is not None
        return self._parser

    def analyze_exclusions(self, repo_path: Path) -> dict:
        """Analyze which files would be excluded for a repository.

        Args:
            repo_path: Path to the git repository.

        Returns:
            Dictionary with exclusion analysis.
        """
        self._ensure_initialized()
        assert self._parser is not None
        return self._parser.analyze_exclusions(repo_path)

    def get_top_repos(
        self,
        start_date: date | None,
        end_date: date | None,
        limit: int = 10,
    ) -> list[tuple[Path, int]]:
        """Get top N repos by net lines changed.

        Args:
            start_date: First day to include (None for no lower bound).
            end_date: Last day to include (None for today).
            limit: Maximum number of repos to return.

        Returns:
            List of (repo_path, net_lines) tuples sorted by net lines descending.
        """
        self._ensure_initialized()
        assert self._repos is not None
        assert self._parser is not None
        assert self._cache is not None

        effective_end = end_date if end_date is not None else date.today()
        repo_stats: list[tuple[Path, int]] = []

        def get_repo_net(repo: Path) -> tuple[Path, int]:
            if start_date is None:
                # Unbounded query - use parser directly
                stats = self._parser.get_stats(repo, start_date, effective_end)
                return (repo, stats.net)
            else:
                # Use cache (create provider without progress callback)
                provider = GitStatsDataProvider(
                    [repo],
                    self._parser,
                    self.STAT_NET,
                    self._cache,
                )
                return (repo, int(provider.get_sum(start_date, effective_end)))

        # Show progress during calculation
        total_repos = len(self._repos)
        with (
            self._progress_context("Analyzing repositories...", total=total_repos) as progress,
            ThreadPoolExecutor(max_workers=8) as executor,
        ):
            futures = {
                executor.submit(get_repo_net, repo): repo
                for repo in self._repos
            }

            for future in as_completed(futures):
                repo = futures[future]
                # Update status with completed repo name and advance progress
                progress.update(
                    self._task_id,
                    status=f"Analyzed: {repo.name}",
                )
                progress.advance(self._task_id)
                repo_stats.append(future.result())

        # Sort by net lines descending and limit
        repo_stats.sort(key=lambda x: x[1], reverse=True)
        return repo_stats[:limit]

    def get_projects_created_in_period(
        self,
        start_date: date | None,
        end_date: date,
    ) -> list[tuple[Path, date]]:
        """Get repositories created (first commit) within a date range.

        Args:
            start_date: First day to include (None for no lower bound).
            end_date: Last day to include.

        Returns:
            List of (repo_path, creation_date) tuples sorted by date ascending.
        """
        self._ensure_initialized()
        assert self._repos is not None
        assert self._parser is not None

        results: list[tuple[Path, date]] = []

        def check_repo(repo: Path) -> tuple[Path, date] | None:
            first_commit = self._parser.get_first_commit_date(repo)
            if first_commit is None:
                return None
            if start_date is not None and first_commit < start_date:
                return None
            if first_commit > end_date:
                return None
            return (repo, first_commit)

        total_repos = len(self._repos)
        with (
            self._progress_context(
                "Finding created projects...", total=total_repos
            ) as progress,
            ThreadPoolExecutor(max_workers=8) as executor,
        ):
            futures = {
                executor.submit(check_repo, repo): repo for repo in self._repos
            }

            for future in as_completed(futures):
                repo = futures[future]
                progress.update(self._task_id, status=f"Checked: {repo.name}")
                progress.advance(self._task_id)
                result = future.result()
                if result is not None:
                    results.append(result)

        # Sort by creation date ascending (oldest first)
        results.sort(key=lambda x: x[1])
        return results

    def get_commits_by_repo_in_period(
        self,
        start_date: date | None,
        end_date: date,
    ) -> list[tuple[Path, int]]:
        """Get commit counts per repository for a date range.

        Args:
            start_date: First day to include (None for no lower bound).
            end_date: Last day to include.

        Returns:
            List of (repo_path, commit_count) tuples sorted by count descending.
            Only includes repos with at least 1 commit.
        """
        self._ensure_initialized()
        assert self._repos is not None
        assert self._parser is not None
        assert self._cache is not None

        results: list[tuple[Path, int]] = []

        def get_repo_commits(repo: Path) -> tuple[Path, int]:
            if start_date is None:
                # Unbounded query - use parser directly
                stats = self._parser.get_stats(repo, start_date, end_date)
                return (repo, stats.commits)
            else:
                # Use cache (create provider without progress callback)
                provider = GitStatsDataProvider(
                    [repo],
                    self._parser,
                    self.STAT_COMMITS,
                    self._cache,
                )
                return (repo, int(provider.get_sum(start_date, end_date)))

        total_repos = len(self._repos)
        with (
            self._progress_context(
                "Counting commits...", total=total_repos
            ) as progress,
            ThreadPoolExecutor(max_workers=8) as executor,
        ):
            futures = {
                executor.submit(get_repo_commits, repo): repo for repo in self._repos
            }

            for future in as_completed(futures):
                repo = futures[future]
                progress.update(self._task_id, status=f"Analyzed: {repo.name}")
                progress.advance(self._task_id)
                repo_path, commit_count = future.result()
                if commit_count > 0:
                    results.append((repo_path, commit_count))

        # Sort by commit count descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def clear_repo_cache(self, repo_path: Path) -> None:
        """Clear all cached data for a repository."""
        self._ensure_initialized()
        assert self._cache is not None
        self._cache.clear_repo(repo_path)

    # Project type management methods

    def get_project_type(self, repo_path: Path) -> tuple[str, str] | None:
        """Get stored project type for a repository.

        Args:
            repo_path: Path to the git repository.

        Returns:
            Tuple of (project_type, type_source) or None if not stored.
            type_source is "auto" or "user".
        """
        self._ensure_initialized()
        assert self._cache is not None
        return self._cache.get_project_type(repo_path)

    def set_project_type(
        self, repo_path: Path, project_type: str, type_source: str = "user"
    ) -> None:
        """Store project type for a repository and clear its cache.

        Clears the cache because stats need recalculation with new rules.

        Args:
            repo_path: Path to the git repository.
            project_type: The project type name (e.g., "unity", "flutter").
            type_source: Either "auto" (detected) or "user" (manually set).
        """
        self._ensure_initialized()
        assert self._cache is not None
        self._cache.set_project_type(repo_path, project_type, type_source)
        self._cache.clear_repo(repo_path)  # Invalidate cache

    def detect_and_store_project_type(self, repo_path: Path) -> str:
        """Detect project type for a repo and store it.

        If type cannot be detected, returns status string for caller to handle.

        Args:
            repo_path: Path to the git repository.

        Returns:
            Detected project type name if successful.
            "ambiguous" if multiple types match (caller should show options).
            "unknown" if no types match (caller should prompt for type).
        """
        self._ensure_initialized()
        detected = detect_project_type(repo_path)
        if detected is not None:
            self.set_project_type(repo_path, detected, "auto")
            return detected

        # Check if it's ambiguous (multiple matches) or unknown (no matches)
        matching = get_matching_types(repo_path)
        if matching:
            return "ambiguous"
        return "unknown"

    def get_matching_project_types(self, repo_path: Path) -> list[str]:
        """Get all project types that match a repository.

        Use this when detect_project_type returns None (ambiguous).

        Args:
            repo_path: Path to the git repository.

        Returns:
            List of matching project type names.
        """
        return get_matching_types(repo_path)

    def get_all_project_types(self) -> list[tuple[str, str, str, str]]:
        """Get all stored project types.

        Returns:
            List of (repo_path, project_type, type_source, detected_at) tuples.
        """
        self._ensure_initialized()
        assert self._cache is not None
        return self._cache.get_all_project_types()

    def get_available_project_types(self) -> list[str]:
        """Get list of all available project type names.

        Returns:
            List of project type names (e.g., ["unity", "flutter", ...]).
        """
        return list(DEFAULT_PROJECT_TYPES.keys())

    def get_parser_for_project_type(self, project_type: str | None) -> GitLogParser:
        """Get or create a parser for a specific project type.

        Args:
            project_type: Project type name, or None for default parser.

        Returns:
            GitLogParser configured for the project type.
        """
        self._ensure_initialized()

        if project_type is None:
            assert self._parser is not None
            return self._parser

        if project_type not in self._parsers:
            config = get_project_type_config(project_type)
            self._parsers[project_type] = GitLogParser(
                self._author,
                list(self._exclude_dirs),
                list(self._exclude_extensions),
                list(self._exclude_filenames),
                project_type_config=config,
            )

        return self._parsers[project_type]

    def analyze_exclusions_for_repo(self, repo_path: Path) -> dict[str, object]:
        """Analyze exclusions using repo's project type config.

        Args:
            repo_path: Path to the git repository.

        Returns:
            Dictionary with exclusion analysis including project type info.
        """
        self._ensure_initialized()

        # Get stored project type or detect it
        stored = self.get_project_type(repo_path)
        if stored:
            project_type = stored[0]
        else:
            # Try to detect
            detected = detect_project_type(repo_path)
            project_type = detected if detected else "generic"

        # Get parser for this project type
        parser = self.get_parser_for_project_type(project_type)
        return parser.analyze_exclusions(repo_path)
