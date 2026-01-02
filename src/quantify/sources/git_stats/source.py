"""Git statistics data source."""

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
)

from quantify.services.stats_calculator import StatsCalculator, TimeStats
from quantify.sources.base import DataProvider, DataSource, SelectableItem, SourceInfo
from quantify.sources.git_stats.data_provider import (
    GitStatsDataProvider,
    ProjectsCreatedDataProvider,
)
from quantify.sources.git_stats.git_log_parser import GitLogParser
from quantify.sources.git_stats.repo_scanner import RepoScanner
from quantify.sources.git_stats.stats_cache import GitStatsCache


class GitStatsSource(DataSource):
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
        self._parser: GitLogParser | None = None
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

    @contextmanager
    def _progress_context(
        self,
        description: str,
        total: int | None = None,
    ) -> Iterator[Progress]:
        """Create a unified progress display context.

        Displays single line: [spinner] status [bar] X/Y

        Args:
            description: Initial status text.
            total: Total count for progress bar, or None for indeterminate.

        Yields:
            Progress instance for updates.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.fields[status]}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=self._console,
            transient=False,
        ) as progress:
            self._progress = progress
            self._task_id = progress.add_task("", total=total, status=description)
            try:
                yield progress
            finally:
                self._progress = None
                self._task_id = None

    def _on_progress(self, repo_name: str, current: int, total: int) -> None:
        """Callback for progress updates during data provider operations.

        Args:
            repo_name: Name of the repository currently being processed.
            current: Current repository index (1-based).
            total: Total number of repositories.
        """
        if self._progress is None or self._task_id is None:
            return

        self._progress.update(
            self._task_id,
            total=total,
            completed=current,
            status=f"Scanning: {repo_name}",
        )

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
