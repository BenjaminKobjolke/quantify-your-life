"""HTML exporter for statistics."""

import shutil
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from quantify.cli.handlers.period_selector import get_period_label
from quantify.config.settings import ExportSettings
from quantify.export.stats_builder import build_chart_data, build_stats_rows
from quantify.export.top_features_exporter import export_top_features
from quantify.services.stats import TimeStats
from quantify.sources.registry import SourceRegistry
from quantify.sources.track_and_graph import TrackAndGraphSource


class HtmlExporter:
    """Exports statistics to HTML files."""

    def __init__(
        self,
        registry: SourceRegistry,
        templates_dir: Path,
        static_dir: Path,
    ) -> None:
        """Initialize HTML exporter.

        Args:
            registry: Source registry with configured sources.
            templates_dir: Path to templates directory.
            static_dir: Path to static files directory.
        """
        self._registry = registry
        self._templates_dir = templates_dir
        self._static_dir = static_dir
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
        )

    def export(self, export_settings: ExportSettings) -> list[Path]:
        """Export configured entries to HTML.

        Args:
            export_settings: Export configuration.

        Returns:
            List of generated file paths.
        """
        output_dir = Path(export_settings.path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy static files
        self._copy_static_files(output_dir)

        generated_files: list[Path] = []
        index_entries: list[dict[str, str]] = []

        # Export each entry
        for entry in export_settings.entries:
            source = self._registry.get_by_id(entry.source)
            if source is None:
                continue

            # Handle top_features entry type specially
            if entry.entry_type == "top_features":
                if not isinstance(source, TrackAndGraphSource):
                    continue
                if entry.entry_id is None or entry.period is None:
                    continue

                # Get group name
                group_name = source.get_item_name(entry.entry_id, "group")
                if group_name is None:
                    continue

                file_path = export_top_features(
                    env=self._env,
                    output_dir=output_dir,
                    source=source,
                    group_id=entry.entry_id,
                    group_name=group_name,
                    period_key=entry.period,
                )
                period_label = get_period_label(entry.period)
                display_name = f"Top Features - {group_name} ({period_label})"
                generated_files.append(file_path)
                index_entries.append({"name": display_name, "filename": file_path.name})
                continue

            # Get item name
            if hasattr(source, "get_item_name"):
                name = source.get_item_name(entry.entry_id, entry.entry_type)
            else:
                items = source.get_selectable_items()
                name = items[0].name if items else entry.source

            if name is None:
                continue

            # Get stats
            stats = source.get_stats(entry.entry_id, entry.entry_type)

            # Determine unit based on entry type (for git stats commits/projects)
            unit = source.info.unit
            unit_label = source.info.unit_label
            if entry.entry_type == "commits":
                unit = "commits"
                unit_label = "commits"
            elif entry.entry_type == "projects_created":
                unit = "projects"
                unit_label = "projects"

            # Export to HTML
            file_path = self._export_stats(
                output_dir=output_dir,
                name=name,
                entry_id=entry.entry_id,
                entry_type=entry.entry_type,
                source_id=entry.source,
                stats=stats,
                unit=unit,
                unit_label=unit_label,
            )
            generated_files.append(file_path)
            index_entries.append({"name": name, "filename": file_path.name})

        # Generate index.html
        index_path = self._export_index(output_dir, index_entries)
        generated_files.insert(0, index_path)

        return generated_files

    def _export_index(self, output_dir: Path, entries: list[dict[str, str]]) -> Path:
        """Generate index.html with links to all exported stats.

        Args:
            output_dir: Output directory path.
            entries: List of dicts with 'name' and 'filename' keys.

        Returns:
            Path to generated index.html.
        """
        template = self._env.get_template("index.html")

        html_content = template.render(
            entries=entries,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

        file_path = output_dir / "index.html"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return file_path

    def _copy_static_files(self, output_dir: Path) -> None:
        """Copy static CSS and JS files to output directory.

        Args:
            output_dir: Output directory path.
        """
        css_dir = output_dir / "css"
        js_dir = output_dir / "js"

        css_dir.mkdir(exist_ok=True)
        js_dir.mkdir(exist_ok=True)

        # Copy CSS files
        src_css = self._static_dir / "css" / "stats.css"
        if src_css.exists():
            shutil.copy(src_css, css_dir / "stats.css")

        # Copy JS files
        src_js = self._static_dir / "js" / "chart.js"
        if src_js.exists():
            shutil.copy(src_js, js_dir / "chart.js")

        src_top_js = self._static_dir / "js" / "top_chart.js"
        if src_top_js.exists():
            shutil.copy(src_top_js, js_dir / "top_chart.js")

    def _export_stats(
        self,
        output_dir: Path,
        name: str,
        entry_id: int | None,
        entry_type: str,
        source_id: str,
        stats: TimeStats,
        unit: str,
        unit_label: str,
    ) -> Path:
        """Export statistics for a single entry.

        Args:
            output_dir: Output directory path.
            name: Name of the item.
            entry_id: ID of the entry.
            entry_type: Type of entry ("group", "feature", "stats").
            source_id: Source identifier.
            stats: Statistics to export.
            unit: Unit type ("time" or "distance").
            unit_label: Unit label for display.

        Returns:
            Path to generated HTML file.
        """
        template = self._env.get_template("stats.html")

        title = name
        stats_rows = build_stats_rows(stats, unit, unit_label)
        chart_labels, chart_values = build_chart_data(stats)

        html_content = template.render(
            title=title,
            stats_rows=[
                {
                    "period": row.period,
                    "value": row.value,
                    "is_separator": row.is_separator,
                    "trend_class": row.trend_class,
                }
                for row in stats_rows
            ],
            chart_labels=chart_labels,
            chart_values=chart_values,
            unit=unit,
            unit_label=unit_label,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

        # Generate filename
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        entry_id_str = str(entry_id) if entry_id is not None else "all"
        filename = f"{source_id}_{entry_type}_{entry_id_str}_{safe_name}.html"
        file_path = output_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return file_path
