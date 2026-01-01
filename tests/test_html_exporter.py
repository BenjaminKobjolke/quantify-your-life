"""Tests for HtmlExporter."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from quantify.config.settings import ExportSettings
from quantify.db.repositories.groups import Group
from quantify.export.html_exporter import HtmlExporter
from quantify.services.stats import TimeStats


@pytest.fixture
def mock_stats() -> TimeStats:
    """Create mock TimeStats."""
    return TimeStats(
        last_7_days=3600.0,
        last_31_days=14400.0,
        avg_per_day_last_30_days=480.0,
        trend_vs_previous_30_days=10.5,
        avg_per_day_last_12_months=500.0,
        avg_per_day_this_year=520.0,
        avg_per_day_last_year=450.0,
        this_week=1800.0,
        this_month=7200.0,
        last_month=6800.0,
        last_12_months=180000.0,
        total=360000.0,
    )


@pytest.fixture
def mock_group() -> Group:
    """Create mock Group."""
    return Group(id=1, name="Test Group", display_index=0, parent_group_id=None, color_index=0)


@pytest.fixture
def setup_exporter(tmp_path: Path) -> tuple[HtmlExporter, Path]:
    """Set up exporter with mock services and temporary directories."""
    templates_dir = tmp_path / "templates"
    static_dir = tmp_path / "static"
    templates_dir.mkdir()
    static_dir.mkdir()
    (static_dir / "css").mkdir()
    (static_dir / "js").mkdir()

    # Create minimal template
    template_content = """<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
<h1>{{ title }}</h1>
{% for row in stats_rows %}
<p>{{ row.period }}: {{ row.value }}</p>
{% endfor %}
<div data-labels='{{ chart_labels | tojson }}' data-values='{{ chart_values | tojson }}'></div>
<p>{{ generated_at }}</p>
</body>
</html>"""
    (templates_dir / "stats.html").write_text(template_content)

    # Create static files
    (static_dir / "css" / "stats.css").write_text("body { margin: 0; }")
    (static_dir / "js" / "chart.js").write_text("// chart")

    mock_stats_service = MagicMock()
    mock_groups_repo = MagicMock()
    mock_features_repo = MagicMock()

    exporter = HtmlExporter(
        stats_service=mock_stats_service,
        groups_repo=mock_groups_repo,
        features_repo=mock_features_repo,
        templates_dir=templates_dir,
        static_dir=static_dir,
    )

    return exporter, tmp_path


def test_export_creates_html_file(
    setup_exporter: tuple[HtmlExporter, Path],
    mock_stats: TimeStats,
    mock_group: Group,
) -> None:
    """Test that export creates HTML file."""
    exporter, tmp_path = setup_exporter
    output_dir = tmp_path / "output"

    exporter._stats.get_group_stats.return_value = mock_stats
    exporter._groups.get_by_id.return_value = mock_group

    export_settings = ExportSettings(
        path=str(output_dir),
        groups=(1,),
        features=(),
    )

    generated = exporter.export(export_settings)

    assert len(generated) == 1
    assert generated[0].exists()
    assert generated[0].suffix == ".html"


def test_export_copies_static_files(
    setup_exporter: tuple[HtmlExporter, Path],
    mock_stats: TimeStats,
    mock_group: Group,
) -> None:
    """Test that export copies static CSS and JS files."""
    exporter, tmp_path = setup_exporter
    output_dir = tmp_path / "output"

    exporter._stats.get_group_stats.return_value = mock_stats
    exporter._groups.get_by_id.return_value = mock_group

    export_settings = ExportSettings(
        path=str(output_dir),
        groups=(1,),
        features=(),
    )

    exporter.export(export_settings)

    assert (output_dir / "css" / "stats.css").exists()
    assert (output_dir / "js" / "chart.js").exists()


def test_export_html_contains_stats(
    setup_exporter: tuple[HtmlExporter, Path],
    mock_stats: TimeStats,
    mock_group: Group,
) -> None:
    """Test that exported HTML contains statistics."""
    exporter, tmp_path = setup_exporter
    output_dir = tmp_path / "output"

    exporter._stats.get_group_stats.return_value = mock_stats
    exporter._groups.get_by_id.return_value = mock_group

    export_settings = ExportSettings(
        path=str(output_dir),
        groups=(1,),
        features=(),
    )

    generated = exporter.export(export_settings)
    content = generated[0].read_text()

    assert "Test Group" in content
    assert "Last 7 days" in content


def test_export_skips_missing_groups(
    setup_exporter: tuple[HtmlExporter, Path],
) -> None:
    """Test that export skips groups not found in database."""
    exporter, tmp_path = setup_exporter
    output_dir = tmp_path / "output"

    exporter._groups.get_by_id.return_value = None

    export_settings = ExportSettings(
        path=str(output_dir),
        groups=(999,),
        features=(),
    )

    generated = exporter.export(export_settings)

    assert len(generated) == 0
