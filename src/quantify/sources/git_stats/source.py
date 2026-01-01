"""Git statistics data source."""

from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn

from quantify.services.stats_calculator import StatsCalculator, TimeStats
from quantify.sources.base import DataProvider, DataSource, SelectableItem, SourceInfo
from quantify.sources.git_stats.data_provider import GitStatsDataProvider
from quantify.sources.git_stats.git_log_parser import GitLogParser
from quantify.sources.git_stats.repo_scanner import RepoScanner
from quantify.sources.git_stats.stats_cache import GitStatsCache


class GitStatsSource(DataSource):
    """Data source for git line statistics across repositories."""

    # Stat type constants
    STAT_ADDED = "added"
    STAT_REMOVED = "removed"
    STAT_NET = "net"

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
        """Return three stat items: Lines Added, Lines Removed, Net Lines."""
        return [
            SelectableItem(None, "Git: Lines Added", self.STAT_ADDED),
            SelectableItem(None, "Git: Lines Removed", self.STAT_REMOVED),
            SelectableItem(None, "Git: Net Lines", self.STAT_NET),
        ]

    def get_item_name(self, item_id: int | None, item_type: str) -> str | None:
        """Get the name of an item by type.

        Args:
            item_id: Not used (always None for git stats).
            item_type: "added", "removed", or "net".

        Returns:
            The item name, or None if not found.
        """
        names = {
            self.STAT_ADDED: "Git: Lines Added",
            self.STAT_REMOVED: "Git: Lines Removed",
            self.STAT_NET: "Git: Net Lines",
        }
        return names.get(item_type)

    def get_data_provider(
        self, item_id: int | None = None, item_type: str | None = None
    ) -> DataProvider:
        """Get a data provider for the specified stat type.

        Args:
            item_id: Not used (always None for git stats).
            item_type: "added", "removed", or "net".

        Returns:
            GitStatsDataProvider for the requested stat type.
        """
        self._ensure_initialized()
        stat_type = item_type or self.STAT_NET
        assert self._repos is not None
        assert self._parser is not None
        assert self._cache is not None

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

        # Show progress during calculation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self._console,
            transient=True,
        ) as progress:
            self._progress = progress
            self._task_id = progress.add_task("Scanning repositories...", total=None)
            try:
                return calculator.calculate(provider.get_sum)
            finally:
                self._progress = None
                self._task_id = None

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

    def _on_progress(self, repo_name: str, current: int, total: int) -> None:
        """Callback for progress updates during data provider operations.

        Args:
            repo_name: Name of the repository currently being processed.
            current: Current repository index (1-based).
            total: Total number of repositories.
        """
        if self._progress is not None and self._task_id is not None:
            self._progress.update(
                self._task_id,
                description=f"Scanning {repo_name} ({current}/{total})...",
            )
