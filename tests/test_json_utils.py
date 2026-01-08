"""Tests for JsonUtils."""

import json
from pathlib import Path

import pytest

from quantify.utils.json_utils import JsonUtils


class TestDeepMerge:
    """Tests for JsonUtils.deep_merge."""

    def test_empty_dicts(self) -> None:
        """Test merging empty dictionaries."""
        result = JsonUtils.deep_merge({}, {})
        assert result == {}

    def test_override_replaces_empty_base(self) -> None:
        """Test that override replaces empty base."""
        result = JsonUtils.deep_merge({}, {"key": "value"})
        assert result == {"key": "value"}

    def test_base_preserved_with_empty_override(self) -> None:
        """Test that base is preserved with empty override."""
        result = JsonUtils.deep_merge({"key": "value"}, {})
        assert result == {"key": "value"}

    def test_scalar_override(self) -> None:
        """Test that scalar values are overridden."""
        base = {"key": "base_value"}
        override = {"key": "override_value"}
        result = JsonUtils.deep_merge(base, override)
        assert result == {"key": "override_value"}

    def test_new_keys_added(self) -> None:
        """Test that new keys from override are added."""
        base = {"key1": "value1"}
        override = {"key2": "value2"}
        result = JsonUtils.deep_merge(base, override)
        assert result == {"key1": "value1", "key2": "value2"}

    def test_nested_dict_merge(self) -> None:
        """Test that nested dictionaries are merged recursively."""
        base = {"outer": {"inner1": "value1"}}
        override = {"outer": {"inner2": "value2"}}
        result = JsonUtils.deep_merge(base, override)
        assert result == {"outer": {"inner1": "value1", "inner2": "value2"}}

    def test_nested_dict_override(self) -> None:
        """Test that nested values can be overridden."""
        base = {"outer": {"inner": "base_value"}}
        override = {"outer": {"inner": "override_value"}}
        result = JsonUtils.deep_merge(base, override)
        assert result == {"outer": {"inner": "override_value"}}

    def test_array_replaced_not_merged(self) -> None:
        """Test that arrays are replaced entirely, not merged."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result = JsonUtils.deep_merge(base, override)
        assert result == {"items": [4, 5]}

    def test_complex_nested_structure(self) -> None:
        """Test merging complex nested structures."""
        base = {
            "sources": {
                "git_stats": {
                    "author": "Base Author",
                    "root_paths": ["/base/path"],
                }
            },
            "export": {
                "path": "/base/export",
            },
        }
        override = {
            "sources": {
                "git_stats": {
                    "root_paths": ["/override/path"],
                }
            },
            "export": {
                "entries": [{"source": "test", "type": "group", "id": 1}],
            },
        }
        result = JsonUtils.deep_merge(base, override)

        assert result["sources"]["git_stats"]["author"] == "Base Author"
        assert result["sources"]["git_stats"]["root_paths"] == ["/override/path"]
        assert result["export"]["path"] == "/base/export"
        assert result["export"]["entries"] == [
            {"source": "test", "type": "group", "id": 1}
        ]

    def test_does_not_modify_originals(self) -> None:
        """Test that original dicts are not modified."""
        base = {"key": "base_value"}
        override = {"key": "override_value"}
        original_base = base.copy()
        original_override = override.copy()

        JsonUtils.deep_merge(base, override)

        assert base == original_base
        assert override == original_override


class TestLoadJson:
    """Tests for JsonUtils.load_json."""

    def test_load_valid_json(self, tmp_path: Path) -> None:
        """Test loading valid JSON file."""
        json_path = tmp_path / "test.json"
        json_path.write_text('{"key": "value"}')

        result = JsonUtils.load_json(json_path)
        assert result == {"key": "value"}

    def test_load_nonexistent_file_raises(self, tmp_path: Path) -> None:
        """Test that loading nonexistent file raises FileNotFoundError."""
        json_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            JsonUtils.load_json(json_path)

    def test_load_invalid_json_raises(self, tmp_path: Path) -> None:
        """Test that loading invalid JSON raises JSONDecodeError."""
        json_path = tmp_path / "invalid.json"
        json_path.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            JsonUtils.load_json(json_path)


class TestLoadAndMerge:
    """Tests for JsonUtils.load_and_merge."""

    def test_merge_both_files(self, tmp_path: Path) -> None:
        """Test merging two JSON files."""
        base_path = tmp_path / "base.json"
        override_path = tmp_path / "override.json"

        base_path.write_text('{"key1": "value1", "key2": "base"}')
        override_path.write_text('{"key2": "override", "key3": "value3"}')

        result = JsonUtils.load_and_merge(base_path, override_path)
        assert result == {"key1": "value1", "key2": "override", "key3": "value3"}

    def test_only_override_when_base_none(self, tmp_path: Path) -> None:
        """Test that only override is used when base_path is None."""
        override_path = tmp_path / "override.json"
        override_path.write_text('{"key": "value"}')

        result = JsonUtils.load_and_merge(None, override_path)
        assert result == {"key": "value"}

    def test_only_override_when_base_not_exists(self, tmp_path: Path) -> None:
        """Test that only override is used when base doesn't exist."""
        base_path = tmp_path / "nonexistent.json"
        override_path = tmp_path / "override.json"
        override_path.write_text('{"key": "value"}')

        result = JsonUtils.load_and_merge(base_path, override_path)
        assert result == {"key": "value"}

    def test_override_not_exists_raises(self, tmp_path: Path) -> None:
        """Test that missing override file raises FileNotFoundError."""
        override_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            JsonUtils.load_and_merge(None, override_path)
