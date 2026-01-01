"""Application settings loaded from config file."""

import json
from dataclasses import dataclass
from pathlib import Path

from quantify.config.constants import Constants


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""


@dataclass(frozen=True)
class ExportSettings:
    """Export configuration settings."""

    path: str
    groups: tuple[int, ...]
    features: tuple[int, ...]


@dataclass(frozen=True)
class Settings:
    """Application settings."""

    db_path: str
    export: ExportSettings | None = None

    @classmethod
    def load(cls, base_dir: Path | None = None) -> "Settings":
        """Load settings from config.json.

        Args:
            base_dir: Base directory containing config.json. Defaults to cwd.

        Returns:
            Settings instance with loaded configuration.

        Raises:
            ConfigError: If config file not found or invalid.
        """
        if base_dir is None:
            base_dir = Path.cwd()

        config_path = base_dir / Constants.CONFIG_FILE_NAME

        if not config_path.exists():
            raise ConfigError(Constants.ERROR_CONFIG_NOT_FOUND.format(path=config_path))

        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        db_path = data.get("db_path")
        if not db_path:
            raise ConfigError("db_path is required in config.json")

        export_settings = None
        export_data = data.get("export")
        if export_data:
            export_settings = ExportSettings(
                path=export_data.get("path", ""),
                groups=tuple(export_data.get("groups", [])),
                features=tuple(export_data.get("features", [])),
            )

        return cls(db_path=db_path, export=export_settings)
