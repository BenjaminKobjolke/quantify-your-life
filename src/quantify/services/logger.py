"""Centralized logging with rotating file support."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from quantify.config.constants import Constants


class Logger:
    """Singleton logger with rotating file handler."""

    _instance: "Logger | None" = None
    _initialized: bool = False

    # Use home dir for logs (same as cache)
    LOG_DIR = Path.home() / ".quantify-your-life" / Constants.LOG_DIR_NAME

    def __new__(cls) -> "Logger":
        """Singleton pattern - one logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize logger (only runs once due to singleton)."""
        if Logger._initialized:
            return
        Logger._initialized = True

        self._log_dir = self.LOG_DIR
        self._logger = logging.getLogger("quantify")
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Configure rotating file handler."""
        self._log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self._log_dir / Constants.LOG_FILE_NAME

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=Constants.LOG_MAX_BYTES,
            backupCount=Constants.LOG_BACKUP_COUNT,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(Constants.LOG_FORMAT))

        self._logger.setLevel(logging.DEBUG)
        self._logger.addHandler(file_handler)

    def debug(self, msg: str, *args: Any) -> None:
        """Log debug message."""
        self._logger.debug(msg, *args)

    def info(self, msg: str, *args: Any) -> None:
        """Log info message."""
        self._logger.info(msg, *args)

    def warning(self, msg: str, *args: Any) -> None:
        """Log warning message."""
        self._logger.warning(msg, *args)

    def error(self, msg: str, *args: Any) -> None:
        """Log error message."""
        self._logger.error(msg, *args)

    def exception(self, msg: str, *args: Any) -> None:
        """Log exception with traceback."""
        self._logger.exception(msg, *args)

    @property
    def log_dir(self) -> Path:
        """Get the log directory path."""
        return self._log_dir


def get_logger() -> Logger:
    """Get the singleton logger instance."""
    return Logger()
