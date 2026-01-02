"""Thread-safe SQLite database connection manager."""

import sqlite3
import threading
from collections.abc import Callable
from pathlib import Path


class ThreadLocalDB:
    """Thread-safe SQLite database with thread-local connections.

    Each thread gets its own connection, avoiding SQLite's thread-safety issues.
    Schema initialization is performed once on first connection from any thread.

    Usage:
        db = ThreadLocalDB(Path("data.db"), schema_init=create_tables)
        conn = db.connection  # Get thread-local connection
        conn.execute("SELECT * FROM table")
    """

    def __init__(
        self,
        db_path: Path,
        schema_init: Callable[[sqlite3.Connection], None] | None = None,
    ) -> None:
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file.
            schema_init: Optional callback to initialize schema on first connection.
        """
        self._db_path = db_path
        self._schema_init = schema_init
        self._local = threading.local()
        self._schema_lock = threading.Lock()
        self._schema_initialized = False

    @property
    def connection(self) -> sqlite3.Connection:
        """Get thread-local database connection.

        Creates a new connection for the current thread if needed.
        Initializes schema on first connection from any thread.
        """
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._local.conn = sqlite3.connect(str(self._db_path))
            self._local.conn.row_factory = sqlite3.Row
            self._ensure_schema()

        return self._local.conn

    def _ensure_schema(self) -> None:
        """Initialize schema once (thread-safe)."""
        if self._schema_init is None:
            return

        with self._schema_lock:
            if not self._schema_initialized:
                self._schema_init(self._local.conn)
                self._schema_initialized = True

    def execute(
        self,
        sql: str,
        params: tuple = (),
    ) -> sqlite3.Cursor:
        """Execute SQL and return cursor."""
        return self.connection.execute(sql, params)

    def executemany(
        self,
        sql: str,
        params_seq: list[tuple],
    ) -> sqlite3.Cursor:
        """Execute SQL for each parameter tuple."""
        return self.connection.executemany(sql, params_seq)

    def commit(self) -> None:
        """Commit current transaction."""
        self.connection.commit()

    def close(self) -> None:
        """Close current thread's connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
