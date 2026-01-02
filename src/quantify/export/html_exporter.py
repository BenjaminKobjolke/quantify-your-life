"""HTML exporter for statistics."""

import shutil
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from quantify.config.constants import Constants
from quantify.config.settings import ExportSettings
from quantify.services.stats import TimeStats, format_trend, format_value
from quantify.sources.registry import SourceRegistry


@dataclass
class StatsRow:
    """A row in the stats table."""

    period: str
    value: str
    is_separator: bool = False
    trend_class: str = ""


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
        stats_rows = self._build_stats_rows(stats, unit, unit_label)
        chart_labels, chart_values = self._build_chart_data(stats)

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

    def _build_stats_rows(self, stats: TimeStats, unit: str, unit_label: str) -> list[StatsRow]:
        """Build stats table rows from TimeStats.

        Args:
            stats: Statistics data.
            unit: Unit type ("time" or "distance").
            unit_label: Unit label for display.

        Returns:
            List of stats rows for the template.
        """
        rows: list[StatsRow] = []

        def fmt(value: float) -> str:
            return format_value(value, unit, unit_label)

        def fmt_avg(value: float) -> str:
            return format_value(value, unit, unit_label, is_avg=True)

        # Recent periods
        rows.append(StatsRow(Constants.PERIOD_LAST_7_DAYS, fmt(stats.last_7_days)))
        rows.append(StatsRow(Constants.PERIOD_LAST_31_DAYS, fmt(stats.last_31_days)))

        # Separator
        rows.append(StatsRow("", "", is_separator=True))

        # Averages
        rows.append(
            StatsRow(
                Constants.PERIOD_AVG_LAST_30_DAYS,
                fmt_avg(stats.avg_per_day_last_30_days),
            )
        )

        # Trend with color class
        trend_str = format_trend(stats.trend_vs_previous_30_days)
        trend_class = ""
        if stats.trend_vs_previous_30_days is not None:
            is_positive = stats.trend_vs_previous_30_days >= 0
            trend_class = "trend-positive" if is_positive else "trend-negative"
        rows.append(StatsRow(Constants.PERIOD_TREND_30_DAYS, trend_str, trend_class=trend_class))

        # Separator
        rows.append(StatsRow("", "", is_separator=True))

        rows.append(
            StatsRow(
                Constants.PERIOD_AVG_LAST_12_MONTHS,
                fmt_avg(stats.avg_per_day_last_12_months),
            )
        )
        rows.append(
            StatsRow(
                Constants.PERIOD_AVG_THIS_YEAR,
                fmt_avg(stats.avg_per_day_this_year),
            )
        )
        rows.append(
            StatsRow(
                Constants.PERIOD_AVG_LAST_YEAR,
                fmt_avg(stats.avg_per_day_last_year),
            )
        )

        # Separator
        rows.append(StatsRow("", "", is_separator=True))

        # Yearly totals
        current_year = date.today().year
        rows.append(
            StatsRow(
                Constants.PERIOD_TOTAL_THIS_YEAR.format(year=current_year),
                fmt(stats.total_this_year),
            )
        )
        rows.append(
            StatsRow(
                Constants.PERIOD_TOTAL_LAST_YEAR.format(year=current_year - 1),
                fmt(stats.total_last_year),
            )
        )
        rows.append(
            StatsRow(
                Constants.PERIOD_TOTAL_YEAR_BEFORE.format(year=current_year - 2),
                fmt(stats.total_year_before),
            )
        )

        # Separator
        rows.append(StatsRow("", "", is_separator=True))

        # Standard periods
        rows.append(StatsRow(Constants.PERIOD_THIS_WEEK, fmt(stats.this_week)))
        rows.append(StatsRow(Constants.PERIOD_THIS_MONTH, fmt(stats.this_month)))
        rows.append(StatsRow(Constants.PERIOD_LAST_MONTH, fmt(stats.last_month)))
        rows.append(StatsRow(Constants.PERIOD_LAST_12_MONTHS, fmt(stats.last_12_months)))
        rows.append(StatsRow(Constants.PERIOD_TOTAL, fmt(stats.total)))

        return rows

    def _build_chart_data(self, stats: TimeStats) -> tuple[list[str], list[float]]:
        """Build chart data from TimeStats.

        Args:
            stats: Statistics data.

        Returns:
            Tuple of (labels, values) for the chart.
        """
        labels = [
            "Last 7d",
            "This Week",
            "This Month",
            "Last Month",
            "Last 31d",
        ]
        values = [
            stats.last_7_days,
            stats.this_week,
            stats.this_month,
            stats.last_month,
            stats.last_31_days,
        ]
        return labels, values
