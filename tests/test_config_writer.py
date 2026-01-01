"""Tests for ConfigWriter."""

import json
from pathlib import Path

import pytest

from quantify.config.config_writer import ConfigWriter


@pytest.fixture
def temp_config(tmp_path: Path) -> Path:
    """Create a temporary config file."""
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"db_path": "test.db"}))
    return config_path


@pytest.fixture
def config_writer(temp_config: Path) -> ConfigWriter:
    """Create a ConfigWriter with temporary config."""
    return ConfigWriter(temp_config)


def test_add_export_group(config_writer: ConfigWriter, temp_config: Path) -> None:
    """Test adding a group to export config."""
    result = config_writer.add_export_group(42)
    assert result is True

    config = json.loads(temp_config.read_text())
    assert config["export"]["groups"] == [42]


def test_add_export_group_duplicate(config_writer: ConfigWriter) -> None:
    """Test adding duplicate group returns False."""
    config_writer.add_export_group(42)
    result = config_writer.add_export_group(42)
    assert result is False


def test_remove_export_group(config_writer: ConfigWriter, temp_config: Path) -> None:
    """Test removing a group from export config."""
    config_writer.add_export_group(42)
    result = config_writer.remove_export_group(42)
    assert result is True

    config = json.loads(temp_config.read_text())
    assert config["export"]["groups"] == []


def test_remove_export_group_not_found(config_writer: ConfigWriter) -> None:
    """Test removing non-existent group returns False."""
    result = config_writer.remove_export_group(42)
    assert result is False


def test_add_export_feature(config_writer: ConfigWriter, temp_config: Path) -> None:
    """Test adding a feature to export config."""
    result = config_writer.add_export_feature(101)
    assert result is True

    config = json.loads(temp_config.read_text())
    assert config["export"]["features"] == [101]


def test_add_export_feature_duplicate(config_writer: ConfigWriter) -> None:
    """Test adding duplicate feature returns False."""
    config_writer.add_export_feature(101)
    result = config_writer.add_export_feature(101)
    assert result is False


def test_remove_export_feature(config_writer: ConfigWriter, temp_config: Path) -> None:
    """Test removing a feature from export config."""
    config_writer.add_export_feature(101)
    result = config_writer.remove_export_feature(101)
    assert result is True

    config = json.loads(temp_config.read_text())
    assert config["export"]["features"] == []


def test_set_export_path(config_writer: ConfigWriter, temp_config: Path) -> None:
    """Test setting export path."""
    config_writer.set_export_path("/path/to/export")

    config = json.loads(temp_config.read_text())
    assert config["export"]["path"] == "/path/to/export"


def test_get_export_groups(config_writer: ConfigWriter) -> None:
    """Test getting configured export groups."""
    config_writer.add_export_group(1)
    config_writer.add_export_group(2)

    groups = config_writer.get_export_groups()
    assert groups == [1, 2]


def test_get_export_features(config_writer: ConfigWriter) -> None:
    """Test getting configured export features."""
    config_writer.add_export_feature(10)
    config_writer.add_export_feature(20)

    features = config_writer.get_export_features()
    assert features == [10, 20]


def test_get_export_path(config_writer: ConfigWriter) -> None:
    """Test getting configured export path."""
    config_writer.set_export_path("/my/path")

    path = config_writer.get_export_path()
    assert path == "/my/path"


def test_get_export_path_empty(config_writer: ConfigWriter) -> None:
    """Test getting export path when not set."""
    path = config_writer.get_export_path()
    assert path == ""
