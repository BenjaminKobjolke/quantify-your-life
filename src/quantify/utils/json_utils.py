"""JSON utility functions for configuration handling."""

import json
from pathlib import Path
from typing import Any


class JsonUtils:
    """Utility class for JSON operations including deep merging."""

    @staticmethod
    def deep_merge(
        base: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        """Deep merge two dictionaries.

        Override values take precedence over base values.
        - Dictionaries: recursively merged
        - Arrays: replaced entirely (not merged)
        - Scalars: overridden

        Args:
            base: The base dictionary with default values.
            override: The override dictionary with values to merge in.

        Returns:
            A new merged dictionary.
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = JsonUtils.deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def load_json(path: Path) -> dict[str, Any]:
        """Load a JSON file and return its contents as a dictionary.

        Args:
            path: Path to the JSON file.

        Returns:
            Dictionary containing the JSON data.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        with open(path, encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
            return result

    @staticmethod
    def load_and_merge(
        base_path: Path | None,
        override_path: Path,
    ) -> dict[str, Any]:
        """Load and merge two JSON files.

        If base_path is None or doesn't exist, only override_path is loaded.

        Args:
            base_path: Optional path to the base JSON file.
            override_path: Path to the override JSON file.

        Returns:
            Merged dictionary with override values taking precedence.

        Raises:
            FileNotFoundError: If override_path does not exist.
            json.JSONDecodeError: If either file contains invalid JSON.
        """
        base_data: dict[str, Any] = {}

        if base_path and base_path.exists():
            base_data = JsonUtils.load_json(base_path)

        override_data = JsonUtils.load_json(override_path)

        result: dict[str, Any] = JsonUtils.deep_merge(base_data, override_data)
        return result
