"""Tests for HtmlExporter."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from quantify.config.settings import ExportEntry, ExportSettings
from quantify.export.html_exporter import HtmlExporter
from quantify.services.stats_calculator import TimeStats
from quantify.sources.base import DataSource, SourceInfo
from quantify.sources.registry import SourceRegistry


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
def mock_source(mock_stats: TimeStats) -> MagicMock:
    """Create a mock DataSource."""
    source = MagicMock(spec=DataSource)
    source.info = SourceInfo(
        id="track_and_graph",
        display_name="Track & Graph",
        unit="time",
        unit_label="h",
    )
    source.get_item_name.return_value = "Test Group"
    source.get_stats.return_value = mock_stats
    source.is_configured.return_value = True
    return source


@pytest.fixture
def setup_exporter(tmp_path: Path, mock_source: MagicMock) -> tuple[HtmlExporter, Path]:
    """Set up exporter with mock services and temporary directories."""
    templates_dir = tmp_path / "templates"
    static_dir = tmp_path / "static"
    templates_dir.mkdir()
    static_dir.mkdir()
    (static_dir / "css").mkdir()
    (static_dir / "js").mkdir()

    # Create minimal stats template
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

    # Create minimal index template
    index_template = """<!DOCTYPE html>
<html>
<head><title>Index</title></head>
<body>
{% for entry in entries %}
<a href="{{ entry.filename }}">{{ entry.name }}</a>
{% endfor %}
</body>
</html>"""
    (templates_dir / "index.html").write_text(index_template)

    # Create static files
    (static_dir / "css" / "stats.css").write_text("body { margin: 0; }")
    (static_dir / "js" / "chart.js").write_text("// chart")

    # Create registry with mock source
    registry = SourceRegistry()
    registry.register(mock_source)

    exporter = HtmlExporter(
        registry=registry,
        templates_dir=templates_dir,
        static_dir=static_dir,
    )

    return exporter, tmp_path


def test_export_creates_html_file(
    setup_exporter: tuple[HtmlExporter, Path],
    mock_stats: TimeStats,
) -> None:
    """Test that export creates HTML file."""
    exporter, tmp_path = setup_exporter
    output_dir = tmp_path / "output"

    export_settings = ExportSettings(
        path=str(output_dir),
        entries=(
            ExportEntry(source="track_and_graph", entry_type="group", entry_id=1),
        ),
    )

    generated = exporter.export(export_settings)

    # First file is index.html, second is the stats file
    assert len(generated) == 2
    assert generated[0].name == "index.html"
    assert generated[1].exists()
    assert generated[1].suffix == ".html"


def test_export_copies_static_files(
    setup_exporter: tuple[HtmlExporter, Path],
    mock_stats: TimeStats,
) -> None:
    """Test that export copies static CSS and JS files."""
    exporter, tmp_path = setup_exporter
    output_dir = tmp_path / "output"

    export_settings = ExportSettings(
        path=str(output_dir),
        entries=(
            ExportEntry(source="track_and_graph", entry_type="group", entry_id=1),
        ),
    )

    exporter.export(export_settings)

    assert (output_dir / "css" / "stats.css").exists()
    assert (output_dir / "js" / "chart.js").exists()


def test_export_html_contains_stats(
    setup_exporter: tuple[HtmlExporter, Path],
    mock_stats: TimeStats,
) -> None:
    """Test that exported HTML contains statistics."""
    exporter, tmp_path = setup_exporter
    output_dir = tmp_path / "output"

    export_settings = ExportSettings(
        path=str(output_dir),
        entries=(
            ExportEntry(source="track_and_graph", entry_type="group", entry_id=1),
        ),
    )

    generated = exporter.export(export_settings)
    # generated[0] is index.html, generated[1] is the stats file
    content = generated[1].read_text()

    assert "Test Group" in content
    assert "Last 7 days" in content


def test_export_skips_missing_sources(
    tmp_path: Path,
) -> None:
    """Test that export skips entries for sources not in registry."""
    templates_dir = tmp_path / "templates"
    static_dir = tmp_path / "static"
    templates_dir.mkdir()
    static_dir.mkdir()
    (static_dir / "css").mkdir()
    (static_dir / "js").mkdir()

    # Create minimal templates
    (templates_dir / "stats.html").write_text("<html></html>")
    index_content = "<html>{% for e in entries %}{{ e.name }}{% endfor %}</html>"
    (templates_dir / "index.html").write_text(index_content)

    # Empty registry
    registry = SourceRegistry()

    exporter = HtmlExporter(
        registry=registry,
        templates_dir=templates_dir,
        static_dir=static_dir,
    )

    output_dir = tmp_path / "output"
    export_settings = ExportSettings(
        path=str(output_dir),
        entries=(
            ExportEntry(source="nonexistent", entry_type="group", entry_id=999),
        ),
    )

    generated = exporter.export(export_settings)

    # Only index.html is generated (no stats files since source not found)
    assert len(generated) == 1
    assert generated[0].name == "index.html"


def test_export_hometrainer_format(
    tmp_path: Path,
    mock_stats: TimeStats,
) -> None:
    """Test that Hometrainer exports use distance formatting."""
    templates_dir = tmp_path / "templates"
    static_dir = tmp_path / "static"
    templates_dir.mkdir()
    static_dir.mkdir()
    (static_dir / "css").mkdir()
    (static_dir / "js").mkdir()

    template_content = """<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
{% for row in stats_rows %}
<p>{{ row.period }}: {{ row.value }}</p>
{% endfor %}
</body>
</html>"""
    (templates_dir / "stats.html").write_text(template_content)
    index_content = "<html>{% for e in entries %}{{ e.name }}{% endfor %}</html>"
    (templates_dir / "index.html").write_text(index_content)

    # Create hometrainer mock source
    ht_source = MagicMock(spec=DataSource)
    ht_source.info = SourceInfo(
        id="hometrainer",
        display_name="Hometrainer",
        unit="distance",
        unit_label="km",
    )
    ht_source.get_item_name.return_value = "Hometrainer (km)"
    ht_source.get_stats.return_value = mock_stats
    ht_source.is_configured.return_value = True

    registry = SourceRegistry()
    registry.register(ht_source)

    exporter = HtmlExporter(
        registry=registry,
        templates_dir=templates_dir,
        static_dir=static_dir,
    )

    output_dir = tmp_path / "output"
    export_settings = ExportSettings(
        path=str(output_dir),
        entries=(
            ExportEntry(source="hometrainer", entry_type="stats", entry_id=None),
        ),
    )

    generated = exporter.export(export_settings)
    # generated[0] is index.html, generated[1] is the stats file
    content = generated[1].read_text()

    # Should use distance format (km) not time format (h m)
    assert "km" in content
    assert "Hometrainer" in content
