"""SQLite cache for git statistics."""

import logging
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from quantify.services.db import ThreadLocalDB
from quantify.sources.git_stats.git_log_parser import GitStats

logger = logging.getLogger(__name__)


class GitStatsCache:
    """Caches daily git stats in SQLite to avoid repeated git queries.

    Design decisions:
    - Today's date is NEVER cached (commits may still be added)
    - Unbounded queries (no start_date) skip the cache entirely
    - Empty results are cached as (0, 0) to avoid re-querying empty repos/days
    - repo_path is stored as absolute path string for consistency

    Thread Safety:
    - Uses ThreadLocalDB for thread-local connections
    - SQLite handles file-level locking for concurrent writes
    """

    # SQL Queries
    _SQL_SUM = """
        SELECT COALESCE(SUM(added), 0) as total_added,
               COALESCE(SUM(removed), 0) as total_removed,
               COALESCE(SUM(commits), 0) as total_commits
        FROM daily_stats
        WHERE repo_path = ? AND date >= ? AND date <= ?
    """

    _SQL_DATES = """
        SELECT date FROM daily_stats
        WHERE repo_path = ? AND date >= ? AND date <= ?
    """

    _SQL_UPSERT = """
        INSERT OR REPLACE INTO daily_stats (repo_path, date, added, removed, commits)
        VALUES (?, ?, ?, ?, ?)
    """

    def __init__(self, db_path: Path) -> None:
        """Initialize cache with database path."""
        self._db = ThreadLocalDB(db_path, self._init_schema)

    @staticmethod
    def _init_schema(conn: sqlite3.Connection) -> None:
        """Create tables and migrate schema."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                repo_path TEXT NOT NULL,
                date TEXT NOT NULL,
                added INTEGER NOT NULL,
                removed INTEGER NOT NULL,
                commits INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (repo_path, date)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_stats_repo ON daily_stats(repo_path)
        """)
        conn.commit()

        # Migrate: add commits column if missing
        cursor = conn.execute("PRAGMA table_info(daily_stats)")
        columns = {row["name"] for row in cursor.fetchall()}
        if "commits" not in columns:
            conn.execute("ALTER TABLE daily_stats ADD COLUMN commits INTEGER NOT NULL DEFAULT 0")
            conn.commit()
            logger.info("Migrated daily_stats table: added commits column")

    @staticmethod
    def _repo_key(repo_path: Path) -> str:
        """Convert repo path to cache key."""
        return str(repo_path.resolve())

    @staticmethod
    def _yesterday() -> date:
        """Get yesterday's date (last cacheable day)."""
        return date.today() - timedelta(days=1)

    def get_cached_sum(
        self,
        repo_path: Path,
        start_date: date,
        end_date: date,
    ) -> tuple[int, int, int]:
        """Get sum of cached added/removed/commits for date range.

        Only returns data for dates in cache. Missing dates excluded.
        """
        effective_end = min(end_date, self._yesterday())
        if effective_end < start_date:
            return (0, 0, 0)

        row = self._db.execute(
            self._SQL_SUM,
            (self._repo_key(repo_path), start_date.isoformat(), effective_end.isoformat()),
        ).fetchone()

        return (row["total_added"], row["total_removed"], row["total_commits"])

    def get_cached_dates(
        self,
        repo_path: Path,
        start_date: date,
        end_date: date,
    ) -> set[date]:
        """Get set of dates already cached for this repo."""
        rows = self._db.execute(
            self._SQL_DATES,
            (self._repo_key(repo_path), start_date.isoformat(), end_date.isoformat()),
        ).fetchall()

        return {date.fromisoformat(row["date"]) for row in rows}

    def get_missing_dates(
        self,
        repo_path: Path,
        start_date: date,
        end_date: date,
    ) -> list[date]:
        """Return dates not yet cached for this repo.

        Today is always included (never cached). Future dates excluded.
        """
        today = date.today()
        effective_end = min(end_date, today)

        if effective_end < start_date:
            return []

        # Generate all dates in range
        all_dates = {
            start_date + timedelta(days=i)
            for i in range((effective_end - start_date).days + 1)
        }

        # Get cached dates (today always considered missing)
        cached = self.get_cached_dates(repo_path, start_date, effective_end)
        cached.discard(today)

        return sorted(all_dates - cached)

    def save_daily_stats(
        self,
        repo_path: Path,
        day: date,
        stats: GitStats,
    ) -> None:
        """Save stats for a single day. Skips today/future."""
        if day >= date.today():
            logger.debug(f"Skipping cache for today or future: {day}")
            return

        self._db.execute(
            self._SQL_UPSERT,
            (self._repo_key(repo_path), day.isoformat(), stats.added, stats.removed, stats.commits),
        )
        self._db.commit()

    def save_batch(
        self,
        repo_path: Path,
        daily_stats: dict[date, GitStats],
    ) -> None:
        """Save multiple days in a single transaction. Excludes today/future."""
        today = date.today()
        repo_key = self._repo_key(repo_path)

        entries = [
            (repo_key, day.isoformat(), stats.added, stats.removed, stats.commits)
            for day, stats in daily_stats.items()
            if day < today
        ]

        if entries:
            self._db.executemany(self._SQL_UPSERT, entries)
            self._db.commit()

    def clear_repo(self, repo_path: Path) -> None:
        """Remove all cached data for a repository."""
        self._db.execute(
            "DELETE FROM daily_stats WHERE repo_path = ?",
            (self._repo_key(repo_path),),
        )
        self._db.commit()

    def clear_all(self) -> None:
        """Remove all cached data."""
        self._db.execute("DELETE FROM daily_stats")
        self._db.commit()

    def close(self) -> None:
        """Close current thread's database connection."""
        self._db.close()
