"""Log file reader for Hometrainer data."""

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass
class LogEntry:
    """A single log entry from a Hometrainer log file."""

    log_date: date
    miles: float


class HometrainerLogReader:
    """Reads Hometrainer log files.

    Log files are organized as:
    - {base_path}/{YYYY}/{YYYY_MM_DD}.txt
    - Each file contains a single float value representing miles
    """

    def __init__(self, logs_path: Path) -> None:
        """Initialize log reader.

        Args:
            logs_path: Base path to the Hometrainer_Logs directory.
        """
        self._logs_path = logs_path

    def _get_log_file_path(self, d: date) -> Path:
        """Get the path to a log file for a specific date.

        Args:
            d: The date to get the log file for.

        Returns:
            Path to the log file.
        """
        year_dir = str(d.year)
        filename = f"{d.year}_{d.month:02d}_{d.day:02d}.txt"
        return self._logs_path / year_dir / filename

    def _read_log_file(self, file_path: Path) -> float | None:
        """Read miles value from a log file.

        Args:
            file_path: Path to the log file.

        Returns:
            Miles value or None if file doesn't exist or is invalid.
        """
        if not file_path.exists():
            return None

        try:
            content = file_path.read_text().strip()
            if not content:
                return None
            return float(content)
        except (ValueError, OSError):
            return None

    def get_entry(self, d: date) -> LogEntry | None:
        """Get log entry for a specific date.

        Args:
            d: The date to get the entry for.

        Returns:
            LogEntry or None if no entry exists.
        """
        file_path = self._get_log_file_path(d)
        miles = self._read_log_file(file_path)
        if miles is None:
            return None
        return LogEntry(log_date=d, miles=miles)

    def get_entries(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[LogEntry]:
        """Get all log entries within a date range.

        Args:
            start_date: First day to include (None for earliest available).
            end_date: Last day to include (None for today).

        Returns:
            List of log entries in the range.
        """
        if end_date is None:
            end_date = date.today()

        # If no start date, find earliest year directory
        if start_date is None:
            start_date = self._find_earliest_date()
            if start_date is None:
                return []

        entries: list[LogEntry] = []
        current = start_date

        while current <= end_date:
            entry = self.get_entry(current)
            if entry is not None:
                entries.append(entry)
            current += timedelta(days=1)

        return entries

    def _find_earliest_date(self) -> date | None:
        """Find the earliest date with a log file.

        Returns:
            Earliest date or None if no logs exist.
        """
        if not self._logs_path.exists():
            return None

        # Find year directories
        year_dirs = sorted(
            d for d in self._logs_path.iterdir() if d.is_dir() and d.name.isdigit()
        )

        if not year_dirs:
            return None

        # Find earliest log file in earliest year
        for year_dir in year_dirs:
            log_files = sorted(year_dir.glob("*.txt"))
            for log_file in log_files:
                parsed = self._parse_filename(log_file.name)
                if parsed is not None:
                    return parsed

        return None

    def _parse_filename(self, filename: str) -> date | None:
        """Parse a log filename to extract the date.

        Args:
            filename: Filename like "2024_01_15.txt"

        Returns:
            Parsed date or None if invalid format.
        """
        try:
            name = filename.replace(".txt", "")
            parts = name.split("_")
            if len(parts) != 3:
                return None
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            return date(year, month, day)
        except (ValueError, IndexError):
            return None

    def get_sum(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> float:
        """Get total miles in date range.

        Args:
            start_date: First day to include (None for earliest).
            end_date: Last day to include (None for today).

        Returns:
            Sum of miles in the range.
        """
        entries = self.get_entries(start_date, end_date)
        return sum(e.miles for e in entries)
