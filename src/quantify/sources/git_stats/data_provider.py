"""Data provider for git statistics."""

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from quantify.sources.git_stats.git_log_parser import GitLogParser, GitStats

if TYPE_CHECKING:
    from quantify.sources.git_stats.stats_cache import GitStatsCache


# Type alias for progress callback
ProgressCallback = Callable[[str, int, int], None] | None


class GitStatsDataProvider:
    """Provides aggregated git stats across all repositories with caching."""

    def __init__(
        self,
        repos: list[Path],
        git_parser: GitLogParser,
        stat_type: str,
        cache: "GitStatsCache",
        progress_callback: ProgressCallback = None,
    ) -> None:
        """Initialize data provider.

        Args:
            repos: List of repository paths to aggregate.
            git_parser: Parser for extracting git statistics.
            stat_type: Type of stat to return ("added", "removed", or "net").
            cache: SQLite cache for storing/retrieving daily stats.
            progress_callback: Optional callback for progress updates.
                              Signature: callback(repo_name, current, total)
        """
        self._repos = repos
        self._parser = git_parser
        self._stat_type = stat_type
        self._cache = cache
        self._progress_callback = progress_callback

    def get_sum(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> float:
        """Sum stats across all repositories for date range.

        Cache behavior:
        - If start_date is None: Skip cache, query git directly (unbounded query)
        - If end_date is None: Use today as end_date
        - Today's stats are always re-queried from git (never cached)
        - Historical dates use cache, with missing dates fetched from git

        Args:
            start_date: First day to include (None for no lower bound).
            end_date: Last day to include (None for today).

        Returns:
            Sum of the selected stat type across all repos.
        """
        # Handle unbounded queries - skip cache entirely
        if start_date is None:
            return self._get_sum_uncached(start_date, end_date)

        # Normalize end_date
        effective_end = end_date if end_date is not None else date.today()

        total_added = 0
        total_removed = 0
        total_commits = 0
        total_repos = len(self._repos)

        # Skip threading for single repo (avoids nested parallelism)
        if total_repos == 1:
            repo = self._repos[0]
            if self._progress_callback:
                self._progress_callback(repo.name, 1, 1)
            added, removed, commits = self._get_repo_stats_cached(
                repo, start_date, effective_end
            )
            return float(self._compute_stat(added, removed, commits))

        completed = 0
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(
                    self._get_repo_stats_cached, repo, start_date, effective_end
                ): repo
                for repo in self._repos
            }

            for future in as_completed(futures):
                repo = futures[future]
                completed += 1
                if self._progress_callback:
                    self._progress_callback(repo.name, completed, total_repos)

                added, removed, commits = future.result()
                total_added += added
                total_removed += removed
                total_commits += commits

        # Return based on stat type
        return float(self._compute_stat(total_added, total_removed, total_commits))

    def _get_repo_stats_cached(
        self,
        repo: Path,
        start_date: date,
        end_date: date,
    ) -> tuple[int, int, int]:
        """Get stats for a single repo using cache.

        Algorithm:
        1. Get sum of cached dates in range
        2. Find missing dates (not in cache, or today)
        3. Query git for each missing date
        4. Save missing dates to cache (except today)
        5. Add missing stats to cached sum

        Args:
            repo: Repository path.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            Tuple of (total_added, total_removed, total_commits) for the range.
        """
        # 1. Get cached sum for historical dates
        cached_added, cached_removed, cached_commits = self._cache.get_cached_sum(
            repo, start_date, end_date
        )

        # 2. Find dates that need git queries
        missing_dates = self._cache.get_missing_dates(repo, start_date, end_date)

        if not missing_dates:
            return (cached_added, cached_removed, cached_commits)

        # 3. Query git for missing dates and accumulate
        missing_added = 0
        missing_removed = 0
        missing_commits = 0
        today = date.today()
        stats_to_cache: dict[date, GitStats] = {}

        for day in missing_dates:
            stats = self._parser.get_daily_stats(repo, day)
            missing_added += stats.added
            missing_removed += stats.removed
            missing_commits += stats.commits

            # Only cache historical dates, not today
            if day < today:
                stats_to_cache[day] = stats

        # 4. Batch save to cache
        if stats_to_cache:
            self._cache.save_batch(repo, stats_to_cache)

        # 5. Return combined sum
        return (
            cached_added + missing_added,
            cached_removed + missing_removed,
            cached_commits + missing_commits,
        )

    def _get_sum_uncached(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> float:
        """Get sum without using cache (for unbounded queries).

        Used when start_date is None, meaning we need ALL history.
        Cannot efficiently cache this since we don't know the earliest date.

        Args:
            start_date: First day (always None for this method).
            end_date: Last day to include.

        Returns:
            Sum of the selected stat type.
        """
        total_repos = len(self._repos)

        # Skip threading for single repo (avoids nested parallelism)
        if total_repos == 1:
            repo = self._repos[0]
            if self._progress_callback:
                self._progress_callback(repo.name, 1, 1)
            stats = self._parser.get_stats(repo, start_date, end_date)
            return float(self._compute_stat(stats.added, stats.removed, stats.commits))

        total = 0
        completed = 0

        def process_repo(repo: Path) -> int:
            stats = self._parser.get_stats(repo, start_date, end_date)
            return self._compute_stat(stats.added, stats.removed, stats.commits)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(process_repo, repo): repo for repo in self._repos}

            for future in as_completed(futures):
                repo = futures[future]
                completed += 1
                if self._progress_callback:
                    self._progress_callback(repo.name, completed, total_repos)
                total += future.result()

        return float(total)

    def _compute_stat(self, added: int, removed: int, commits: int) -> int:
        """Compute the appropriate stat based on stat_type.

        Args:
            added: Lines added count.
            removed: Lines removed count.
            commits: Commit count.

        Returns:
            The requested stat value.
        """
        if self._stat_type == "added":
            return added
        elif self._stat_type == "removed":
            return removed
        elif self._stat_type == "commits":
            return commits
        else:  # net
            return added - removed


class ProjectsCreatedDataProvider:
    """Provides count of projects created in a date range.

    A project is considered "created" when its first commit by the author
    falls within the queried date range.
    """

    def __init__(
        self,
        repos: list[Path],
        git_parser: GitLogParser,
        progress_callback: ProgressCallback = None,
    ) -> None:
        """Initialize data provider.

        Args:
            repos: List of repository paths to check.
            git_parser: Parser for extracting git statistics.
            progress_callback: Optional callback for progress updates.
        """
        self._repos = repos
        self._parser = git_parser
        self._progress_callback = progress_callback
        self._first_commit_cache: dict[Path, date | None] = {}
        self._cache_lock = threading.Lock()  # Thread safety for _first_commit_cache

    def get_sum(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> float:
        """Count projects created in date range.

        Args:
            start_date: First day to include (None for no lower bound).
            end_date: Last day to include (None for today).

        Returns:
            Number of repos where first commit falls in range.
        """
        effective_end = end_date if end_date is not None else date.today()
        count = 0
        total_repos = len(self._repos)
        completed = 0

        def check_repo(repo: Path) -> int:
            first_commit = self._get_first_commit_date(repo)
            if first_commit is None:
                return 0
            if start_date is not None and first_commit < start_date:
                return 0
            if first_commit > effective_end:
                return 0
            return 1

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(check_repo, repo): repo for repo in self._repos}

            for future in as_completed(futures):
                repo = futures[future]
                completed += 1
                if self._progress_callback:
                    self._progress_callback(repo.name, completed, total_repos)
                count += future.result()

        return float(count)

    def _get_first_commit_date(self, repo: Path) -> date | None:
        """Get cached first commit date for a repo (thread-safe)."""
        with self._cache_lock:
            if repo in self._first_commit_cache:
                return self._first_commit_cache[repo]

        # Fetch outside lock to avoid blocking other threads
        first_commit = self._parser.get_first_commit_date(repo)

        with self._cache_lock:
            self._first_commit_cache[repo] = first_commit
        return first_commit
