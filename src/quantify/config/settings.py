"""Application settings loaded from config file."""

import json
from dataclasses import dataclass
from pathlib import Path

from quantify.config.constants import Constants


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""


# Source-specific configs


@dataclass(frozen=True)
class TrackAndGraphConfig:
    """Configuration for Track & Graph data source."""

    db_path: str


@dataclass(frozen=True)
class HometrainerConfig:
    """Configuration for Hometrainer data source."""

    logs_path: str
    unit: str = "km"  # "km" or "mi"


@dataclass(frozen=True)
class SourcesConfig:
    """Configuration for all data sources."""

    track_and_graph: TrackAndGraphConfig | None = None
    hometrainer: HometrainerConfig | None = None


# Export config


@dataclass(frozen=True)
class ExportEntry:
    """A single entry in the export configuration."""

    source: str  # "track_and_graph" or "hometrainer"
    entry_type: str  # "group", "feature", "stats"
    entry_id: int | None  # None for hometrainer


@dataclass(frozen=True)
class ExportSettings:
    """Export configuration settings."""

    path: str
    entries: tuple[ExportEntry, ...]


# Legacy export settings for backwards compatibility


@dataclass(frozen=True)
class LegacyExportSettings:
    """Legacy export configuration (groups/features without source)."""

    path: str
    groups: tuple[int, ...]
    features: tuple[int, ...]


@dataclass(frozen=True)
class Settings:
    """Application settings."""

    sources: SourcesConfig
    export: ExportSettings | None = None

    @classmethod
    def load(cls, base_dir: Path | None = None) -> "Settings":
        """Load settings from config.json.

        Supports both old format (db_path at root) and new format (sources object).

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
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ConfigError(
                    f"Invalid JSON in {config_path}: {e.msg} at line {e.lineno}, column {e.colno}"
                ) from e

        # Check for new format vs old format
        if "sources" in data:
            return cls._load_new_format(data)
        elif "db_path" in data:
            return cls._load_legacy_format(data)
        else:
            raise ConfigError("Config must have either 'sources' or 'db_path'")

    @classmethod
    def _load_new_format(cls, data: dict) -> "Settings":
        """Load configuration from new format with sources object."""
        sources_data = data.get("sources", {})

        # Track & Graph config
        track_and_graph_config = None
        tg_data = sources_data.get("track_and_graph")
        if tg_data and tg_data.get("db_path"):
            track_and_graph_config = TrackAndGraphConfig(db_path=tg_data["db_path"])

        # Hometrainer config
        hometrainer_config = None
        ht_data = sources_data.get("hometrainer")
        if ht_data and ht_data.get("logs_path"):
            hometrainer_config = HometrainerConfig(
                logs_path=ht_data["logs_path"],
                unit=ht_data.get("unit", "km"),
            )

        sources_config = SourcesConfig(
            track_and_graph=track_and_graph_config,
            hometrainer=hometrainer_config,
        )

        # Export settings
        export_settings = None
        export_data = data.get("export")
        if export_data:
            entries: list[ExportEntry] = []
            for entry_data in export_data.get("entries", []):
                entries.append(
                    ExportEntry(
                        source=entry_data["source"],
                        entry_type=entry_data["type"],
                        entry_id=entry_data.get("id"),
                    )
                )
            export_settings = ExportSettings(
                path=export_data.get("path", ""),
                entries=tuple(entries),
            )

        return cls(sources=sources_config, export=export_settings)

    @classmethod
    def _load_legacy_format(cls, data: dict) -> "Settings":
        """Load configuration from legacy format (db_path at root).

        Converts to new format internally while preserving export entries.
        """
        db_path = data.get("db_path")
        if not db_path:
            raise ConfigError("db_path is required in config.json")

        # Create sources config from legacy db_path
        sources_config = SourcesConfig(
            track_and_graph=TrackAndGraphConfig(db_path=db_path),
            hometrainer=None,
        )

        # Convert legacy export settings to new format
        export_settings = None
        export_data = data.get("export")
        if export_data:
            entries: list[ExportEntry] = []

            # Convert legacy groups to entries
            for group_id in export_data.get("groups", []):
                entries.append(
                    ExportEntry(
                        source="track_and_graph",
                        entry_type="group",
                        entry_id=group_id,
                    )
                )

            # Convert legacy features to entries
            for feature_id in export_data.get("features", []):
                entries.append(
                    ExportEntry(
                        source="track_and_graph",
                        entry_type="feature",
                        entry_id=feature_id,
                    )
                )

            export_settings = ExportSettings(
                path=export_data.get("path", ""),
                entries=tuple(entries),
            )

        return cls(sources=sources_config, export=export_settings)

    @property
    def db_path(self) -> str | None:
        """Get Track & Graph database path (for backwards compatibility)."""
        if self.sources.track_and_graph:
            return self.sources.track_and_graph.db_path
        return None
