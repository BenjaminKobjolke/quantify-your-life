"""SQLite cache for git statistics."""

import logging
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from quantify.sources.git_stats.git_log_parser import GitStats

logger = logging.getLogger(__name__)


class GitStatsCache:
    """Caches daily git stats in SQLite to avoid repeated git queries.

    The cache stores (repo_path, date, added, removed) tuples with a composite
    primary key on (repo_path, date). This allows efficient lookups and avoids
    re-querying git for historical data that never changes.

    Design decisions:
    - Today's date is NEVER cached (commits may still be added)
    - Unbounded queries (no start_date) skip the cache entirely
    - Empty results are cached as (0, 0) to avoid re-querying empty repos/days
    - repo_path is stored as absolute path string for consistency
    """

    def __init__(self, db_path: Path) -> None:
        """Initialize cache with database path.

        Args:
            db_path: Path to SQLite database file. Parent directories
                     will be created if they don't exist.
        """
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def _ensure_connected(self) -> sqlite3.Connection:
        """Ensure database connection exists and schema is created.

        Returns:
            Active database connection.
        """
        if self._conn is None:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row
            self._create_schema()
        return self._conn

    def _create_schema(self) -> None:
        """Create database tables if they don't exist."""
        conn = self._conn
        assert conn is not None

        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                repo_path TEXT NOT NULL,
                date TEXT NOT NULL,
                added INTEGER NOT NULL,
                removed INTEGER NOT NULL,
                PRIMARY KEY (repo_path, date)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_stats_date
            ON daily_stats(date)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_stats_repo
            ON daily_stats(repo_path)
        """)
        conn.commit()

    def get_cached_sum(
        self,
        repo_path: Path,
        start_date: date,
        end_date: date,
    ) -> tuple[int, int]:
        """Get sum of cached added/removed for date range.

        Only returns data for dates that ARE in the cache. Missing dates
        are not included in the sum - caller must handle those separately.

        Args:
            repo_path: Absolute path to the repository.
            start_date: First day to include (inclusive).
            end_date: Last day to include (inclusive).

        Returns:
            Tuple of (total_added, total_removed) for cached dates only.
        """
        conn = self._ensure_connected()

        # Exclude today from cache query - always re-query today
        effective_end = min(end_date, date.today() - timedelta(days=1))

        if effective_end < start_date:
            return (0, 0)

        result = conn.execute(
            """
            SELECT COALESCE(SUM(added), 0) as total_added,
                   COALESCE(SUM(removed), 0) as total_removed
            FROM daily_stats
            WHERE repo_path = ?
              AND date >= ?
              AND date <= ?
            """,
            (str(repo_path.resolve()), start_date.isoformat(), effective_end.isoformat()),
        ).fetchone()

        return (result["total_added"], result["total_removed"])

    def get_cached_dates(
        self,
        repo_path: Path,
        start_date: date,
        end_date: date,
    ) -> set[date]:
        """Get set of dates that are already cached for this repo.

        Args:
            repo_path: Absolute path to the repository.
            start_date: First day to check (inclusive).
            end_date: Last day to check (inclusive).

        Returns:
            Set of dates that have cached data.
        """
        conn = self._ensure_connected()

        rows = conn.execute(
            """
            SELECT date FROM daily_stats
            WHERE repo_path = ?
              AND date >= ?
              AND date <= ?
            """,
            (str(repo_path.resolve()), start_date.isoformat(), end_date.isoformat()),
        ).fetchall()

        return {date.fromisoformat(row["date"]) for row in rows}

    def get_missing_dates(
        self,
        repo_path: Path,
        start_date: date,
        end_date: date,
    ) -> list[date]:
        """Return dates not yet cached for this repo.

        Today is always included in missing dates (never cached).
        Future dates are excluded.

        Args:
            repo_path: Absolute path to the repository.
            start_date: First day to check (inclusive).
            end_date: Last day to check (inclusive).

        Returns:
            Sorted list of dates that need to be queried from git.
        """
        today = date.today()

        # Don't look for future dates
        effective_end = min(end_date, today)

        if effective_end < start_date:
            return []

        # Generate all dates in range
        all_dates: set[date] = set()
        current = start_date
        while current <= effective_end:
            all_dates.add(current)
            current += timedelta(days=1)

        # Get cached dates (excluding today which is never considered cached)
        cached = self.get_cached_dates(repo_path, start_date, effective_end)
        cached.discard(today)  # Today is always "missing"

        # Return sorted list of missing dates
        missing = all_dates - cached
        return sorted(missing)

    def save_daily_stats(
        self,
        repo_path: Path,
        day: date,
        stats: GitStats,
    ) -> None:
        """Save stats for a single day.

        Uses INSERT OR REPLACE to handle updates gracefully.
        Does NOT save today's date (caller should not call this for today).

        Args:
            repo_path: Absolute path to the repository.
            day: The date these stats are for.
            stats: GitStats with added and removed counts.
        """
        # Safety check: never cache today
        if day >= date.today():
            logger.debug(f"Skipping cache for today or future: {day}")
            return

        conn = self._ensure_connected()

        conn.execute(
            """
            INSERT OR REPLACE INTO daily_stats (repo_path, date, added, removed)
            VALUES (?, ?, ?, ?)
            """,
            (str(repo_path.resolve()), day.isoformat(), stats.added, stats.removed),
        )
        conn.commit()

    def save_batch(
        self,
        repo_path: Path,
        daily_stats: dict[date, GitStats],
    ) -> None:
        """Save multiple days of stats in a single transaction.

        More efficient than calling save_daily_stats() repeatedly.
        Automatically excludes today and future dates.

        Args:
            repo_path: Absolute path to the repository.
            daily_stats: Dictionary mapping dates to their stats.
        """
        today = date.today()
        conn = self._ensure_connected()

        # Filter out today and future dates
        valid_entries = [
            (str(repo_path.resolve()), day.isoformat(), stats.added, stats.removed)
            for day, stats in daily_stats.items()
            if day < today
        ]

        if not valid_entries:
            return

        conn.executemany(
            """
            INSERT OR REPLACE INTO daily_stats (repo_path, date, added, removed)
            VALUES (?, ?, ?, ?)
            """,
            valid_entries,
        )
        conn.commit()

    def clear_repo(self, repo_path: Path) -> None:
        """Remove all cached data for a repository.

        Useful if repo is deleted or cache becomes corrupted.

        Args:
            repo_path: Absolute path to the repository.
        """
        conn = self._ensure_connected()
        conn.execute(
            "DELETE FROM daily_stats WHERE repo_path = ?",
            (str(repo_path.resolve()),),
        )
        conn.commit()

    def clear_all(self) -> None:
        """Remove all cached data. Use with caution."""
        conn = self._ensure_connected()
        conn.execute("DELETE FROM daily_stats")
        conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
