"""Configuration file writer for modifying config.json."""

import json
from pathlib import Path
from typing import Any


class ConfigWriter:
    """Handles reading, modifying, and writing config.json."""

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

    def _ensure_export_section(self, config: dict[str, Any]) -> dict[str, Any]:
        """Ensure export section exists in config.

        Args:
            config: Config dictionary.

        Returns:
            Export section dictionary.
        """
        if "export" not in config:
            config["export"] = {"path": "", "groups": [], "features": []}
        export = config["export"]
        if "groups" not in export:
            export["groups"] = []
        if "features" not in export:
            export["features"] = []
        if "path" not in export:
            export["path"] = ""
        result: dict[str, Any] = export
        return result

    def add_export_group(self, group_id: int) -> bool:
        """Add a group ID to export config.

        Args:
            group_id: Group ID to add.

        Returns:
            True if added, False if already exists.
        """
        config = self._read_config()
        export = self._ensure_export_section(config)

        if group_id in export["groups"]:
            return False

        export["groups"].append(group_id)
        self._write_config(config)
        return True

    def remove_export_group(self, group_id: int) -> bool:
        """Remove a group ID from export config.

        Args:
            group_id: Group ID to remove.

        Returns:
            True if removed, False if not found.
        """
        config = self._read_config()
        export = self._ensure_export_section(config)

        if group_id not in export["groups"]:
            return False

        export["groups"].remove(group_id)
        self._write_config(config)
        return True

    def add_export_feature(self, feature_id: int) -> bool:
        """Add a feature ID to export config.

        Args:
            feature_id: Feature ID to add.

        Returns:
            True if added, False if already exists.
        """
        config = self._read_config()
        export = self._ensure_export_section(config)

        if feature_id in export["features"]:
            return False

        export["features"].append(feature_id)
        self._write_config(config)
        return True

    def remove_export_feature(self, feature_id: int) -> bool:
        """Remove a feature ID from export config.

        Args:
            feature_id: Feature ID to remove.

        Returns:
            True if removed, False if not found.
        """
        config = self._read_config()
        export = self._ensure_export_section(config)

        if feature_id not in export["features"]:
            return False

        export["features"].remove(feature_id)
        self._write_config(config)
        return True

    def set_export_path(self, path: str) -> None:
        """Set the export path.

        Args:
            path: Export path to set.
        """
        config = self._read_config()
        export = self._ensure_export_section(config)
        export["path"] = path
        self._write_config(config)

    def get_export_groups(self) -> list[int]:
        """Get configured export group IDs.

        Returns:
            List of group IDs.
        """
        config = self._read_config()
        groups: list[int] = config.get("export", {}).get("groups", [])
        return groups

    def get_export_features(self) -> list[int]:
        """Get configured export feature IDs.

        Returns:
            List of feature IDs.
        """
        config = self._read_config()
        features: list[int] = config.get("export", {}).get("features", [])
        return features

    def get_export_path(self) -> str:
        """Get configured export path.

        Returns:
            Export path or empty string if not set.
        """
        config = self._read_config()
        path: str = config.get("export", {}).get("path", "")
        return path
