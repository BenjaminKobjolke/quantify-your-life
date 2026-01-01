"""Tests for Settings."""

from pathlib import Path

import pytest

from quantify.config.settings import ConfigError, Settings


def test_invalid_json_raises_config_error(tmp_path: Path) -> None:
    """Test that invalid JSON raises ConfigError with helpful message."""
    config_path = tmp_path / "config.json"
    config_path.write_text("{ invalid json }")

    with pytest.raises(ConfigError) as exc_info:
        Settings.load(tmp_path)

    error_msg = str(exc_info.value)
    assert "Invalid JSON" in error_msg
    assert "line" in error_msg
    assert "column" in error_msg


def test_missing_config_raises_config_error(tmp_path: Path) -> None:
    """Test that missing config file raises ConfigError."""
    with pytest.raises(ConfigError) as exc_info:
        Settings.load(tmp_path)

    assert "not found" in str(exc_info.value).lower()


def test_valid_new_format_loads(tmp_path: Path) -> None:
    """Test loading valid new format config."""
    config_path = tmp_path / "config.json"
    config_path.write_text("""{
        "sources": {
            "track_and_graph": {"db_path": "test.db"}
        }
    }""")

    settings = Settings.load(tmp_path)
    assert settings.sources.track_and_graph is not None
    assert settings.sources.track_and_graph.db_path == "test.db"


def test_valid_legacy_format_loads(tmp_path: Path) -> None:
    """Test loading valid legacy format config."""
    config_path = tmp_path / "config.json"
    config_path.write_text('{"db_path": "test.db"}')

    settings = Settings.load(tmp_path)
    assert settings.db_path == "test.db"
