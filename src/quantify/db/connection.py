"""SQLite database connection management."""

import sqlite3
from pathlib import Path
from typing import Any

from quantify.config.constants import Constants


class DatabaseError(Exception):
    """Raised when database operations fail."""


class Database:
    """SQLite database connection manager."""

    def __init__(self, db_path: str) -> None:
        """Initialize database connection.

        Args:
            db_path: Path to the SQLite database file.

        Raises:
            DatabaseError: If database file not found.
        """
        self._db_path = Path(db_path)
        if not self._db_path.exists():
            raise DatabaseError(Constants.ERROR_DB_NOT_FOUND.format(path=db_path))
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        """Get or create database connection.

        Returns:
            Active database connection.
        """
        if self._connection is None:
            self._connection = sqlite3.connect(str(self._db_path))
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        """Execute a query and return all results.

        Args:
            query: SQL query to execute.
            params: Query parameters.

        Returns:
            List of result rows.
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def close(self) -> None:
        """Close the database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
