"""Configuration file writer for modifying config.json."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ExportEntryData:
    """Represents an export entry in the config."""

    source: str
    entry_type: str
    entry_id: int | None
    period: str | None = None


class ConfigWriter:
    """Handles reading, modifying, and writing config.json.

    Supports both legacy format (groups/features arrays) and
    new format (entries array with source).
    """

    def __init__(self, config_path: Path) -> None:
        """Initialize config writer.

        Args:
            config_path: Path to config.json file.
        """
        self._config_path = config_path

    def _read_config(self) -> dict[str, Any]:
        """Read current config from file.

        Returns:
            Config dictionary.
        """
        if not self._config_path.exists():
            return {}

        with open(self._config_path, encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
            return result

    def _write_config(self, config: dict[str, Any]) -> None:
        """Write config to file.

        Args:
            config: Config dictionary to write.
        """
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    def _is_new_format(self, config: dict[str, Any]) -> bool:
        """Check if config uses new format with entries array.

        Args:
            config: Config dictionary.

        Returns:
            True if new format, False if legacy.
        """
        export = config.get("export", {})
        return "entries" in export

    def _ensure_export_section(self, config: dict[str, Any]) -> dict[str, Any]:
        """Ensure export section exists in config.

        For backwards compatibility, maintains legacy format if already present.

        Args:
            config: Config dictionary.

        Returns:
            Export section dictionary.
        """
        if "export" not in config:
            # New configs use new format
            config["export"] = {"path": "", "entries": []}

        export = config["export"]
        if "path" not in export:
            export["path"] = ""

        # For legacy configs, ensure arrays exist
        if not self._is_new_format(config):
            if "groups" not in export:
                export["groups"] = []
            if "features" not in export:
                export["features"] = []

        result: dict[str, Any] = export
        return result

    def _migrate_to_new_format(self, config: dict[str, Any]) -> None:
        """Migrate legacy config to new format.

        Args:
            config: Config dictionary to migrate.
        """
        export = config.get("export", {})
        if self._is_new_format(config):
            return

        entries: list[dict[str, Any]] = []

        # Migrate groups
        for group_id in export.get("groups", []):
            entries.append({
                "source": "track_and_graph",
                "type": "group",
                "id": group_id,
            })

        # Migrate features
        for feature_id in export.get("features", []):
            entries.append({
                "source": "track_and_graph",
                "type": "feature",
                "id": feature_id,
            })

        # Update config
        config["export"] = {
            "path": export.get("path", ""),
            "entries": entries,
        }

    # New format methods

    def add_export_entry(
        self,
        source: str,
        entry_type: str,
        entry_id: int | None,
        period: str | None = None,
    ) -> bool:
        """Add an entry to export config.

        Args:
            source: Source ID (e.g., "track_and_graph", "hometrainer").
            entry_type: Entry type ("group", "feature", "stats", "top_features").
            entry_id: Entry ID (None for hometrainer).
            period: Period key for top_features entries.

        Returns:
            True if added, False if already exists.
        """
        config = self._read_config()
        self._migrate_to_new_format(config)
        self._ensure_export_section(config)

        entries = config["export"]["entries"]

        # Check if entry already exists
        for entry in entries:
            if (
                entry.get("source") == source
                and entry.get("type") == entry_type
                and entry.get("id") == entry_id
                and entry.get("period") == period
            ):
                return False

        entry_data: dict[str, Any] = {
            "source": source,
            "type": entry_type,
            "id": entry_id,
        }
        if period is not None:
            entry_data["period"] = period

        entries.append(entry_data)
        self._write_config(config)
        return True

    def remove_export_entry(
        self,
        source: str,
        entry_type: str,
        entry_id: int | None,
        period: str | None = None,
    ) -> bool:
        """Remove an entry from export config.

        Args:
            source: Source ID.
            entry_type: Entry type.
            entry_id: Entry ID.
            period: Period key for top_features entries.

        Returns:
            True if removed, False if not found.
        """
        config = self._read_config()
        self._migrate_to_new_format(config)
        self._ensure_export_section(config)

        entries = config["export"]["entries"]

        for i, entry in enumerate(entries):
            if (
                entry.get("source") == source
                and entry.get("type") == entry_type
                and entry.get("id") == entry_id
                and entry.get("period") == period
            ):
                entries.pop(i)
                self._write_config(config)
                return True

        return False

    def get_export_entries(self) -> list[ExportEntryData]:
        """Get all configured export entries.

        Returns:
            List of export entries.
        """
        config = self._read_config()

        # Handle legacy format
        if not self._is_new_format(config):
            entries: list[ExportEntryData] = []
            export = config.get("export", {})

            for group_id in export.get("groups", []):
                entries.append(
                    ExportEntryData("track_and_graph", "group", group_id)
                )
            for feature_id in export.get("features", []):
                entries.append(
                    ExportEntryData("track_and_graph", "feature", feature_id)
                )
            return entries

        # New format
        entries = []
        for entry in config.get("export", {}).get("entries", []):
            entries.append(
                ExportEntryData(
                    entry.get("source", ""),
                    entry.get("type", ""),
                    entry.get("id"),
                    entry.get("period"),
                )
            )
        return entries

    # Legacy methods for backwards compatibility

    def add_export_group(self, group_id: int) -> bool:
        """Add a group ID to export config (legacy).

        Args:
            group_id: Group ID to add.

        Returns:
            True if added, False if already exists.
        """
        return self.add_export_entry("track_and_graph", "group", group_id)

    def remove_export_group(self, group_id: int) -> bool:
        """Remove a group ID from export config (legacy).

        Args:
            group_id: Group ID to remove.

        Returns:
            True if removed, False if not found.
        """
        return self.remove_export_entry("track_and_graph", "group", group_id)

    def add_export_feature(self, feature_id: int) -> bool:
        """Add a feature ID to export config (legacy).

        Args:
            feature_id: Feature ID to add.

        Returns:
            True if added, False if already exists.
        """
        return self.add_export_entry("track_and_graph", "feature", feature_id)

    def remove_export_feature(self, feature_id: int) -> bool:
        """Remove a feature ID from export config (legacy).

        Args:
            feature_id: Feature ID to remove.

        Returns:
            True if removed, False if not found.
        """
        return self.remove_export_entry("track_and_graph", "feature", feature_id)

    def set_export_path(self, path: str) -> None:
        """Set the export path.

        Args:
            path: Export path to set.
        """
        config = self._read_config()
        self._ensure_export_section(config)
        config["export"]["path"] = path
        self._write_config(config)

    def get_export_groups(self) -> list[int]:
        """Get configured export group IDs (legacy).

        Returns:
            List of group IDs.
        """
        entries = self.get_export_entries()
        return [
            e.entry_id
            for e in entries
            if e.source == "track_and_graph" and e.entry_type == "group" and e.entry_id is not None
        ]

    def get_export_features(self) -> list[int]:
        """Get configured export feature IDs (legacy).

        Returns:
            List of feature IDs.
        """
        entries = self.get_export_entries()
        return [
            e.entry_id
            for e in entries
            if (e.source == "track_and_graph"
                and e.entry_type == "feature"
                and e.entry_id is not None)
        ]

    def get_export_path(self) -> str:
        """Get configured export path.

        Returns:
            Export path or empty string if not set.
        """
        config = self._read_config()
        path: str = config.get("export", {}).get("path", "")
        return path
