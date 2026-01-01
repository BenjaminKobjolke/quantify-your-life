"""HTML exporter for statistics."""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from quantify.config.constants import Constants
from quantify.config.settings import ExportSettings
from quantify.db.repositories.features import FeaturesRepository
from quantify.db.repositories.groups import GroupsRepository
from quantify.services.stats import StatsService, TimeStats, format_duration, format_trend


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
        stats_service: StatsService,
        groups_repo: GroupsRepository,
        features_repo: FeaturesRepository,
        templates_dir: Path,
        static_dir: Path,
    ) -> None:
        """Initialize HTML exporter.

        Args:
            stats_service: Service for calculating statistics.
            groups_repo: Repository for groups.
            features_repo: Repository for features.
            templates_dir: Path to templates directory.
            static_dir: Path to static files directory.
        """
        self._stats = stats_service
        self._groups = groups_repo
        self._features = features_repo
        self._templates_dir = templates_dir
        self._static_dir = static_dir
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
        )

    def export(self, export_settings: ExportSettings) -> list[Path]:
        """Export configured groups and features to HTML.

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

        # Export groups
        for group_id in export_settings.groups:
            group = self._groups.get_by_id(group_id)
            if group is None:
                continue

            stats = self._stats.get_group_stats(group_id)
            file_path = self._export_stats(
                output_dir=output_dir,
                name=group.name,
                entry_id=group.id,
                entry_type="group",
                stats=stats,
            )
            generated_files.append(file_path)

        # Export features
        for feature_id in export_settings.features:
            feature = self._features.get_by_id(feature_id)
            if feature is None:
                continue

            stats = self._stats.get_feature_stats(feature_id)
            file_path = self._export_stats(
                output_dir=output_dir,
                name=feature.name,
                entry_id=feature.id,
                entry_type="feature",
                stats=stats,
            )
            generated_files.append(file_path)

        return generated_files

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
        entry_id: int,
        entry_type: str,
        stats: TimeStats,
    ) -> Path:
        """Export statistics for a single entry.

        Args:
            output_dir: Output directory path.
            name: Name of the group or feature.
            entry_id: ID of the entry.
            entry_type: Type of entry ("group" or "feature").
            stats: Statistics to export.

        Returns:
            Path to generated HTML file.
        """
        template = self._env.get_template("stats.html")

        title = name
        stats_rows = self._build_stats_rows(stats)
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
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

        # Generate filename
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        filename = f"{entry_type}_{entry_id}_{safe_name}.html"
        file_path = output_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return file_path

    def _build_stats_rows(self, stats: TimeStats) -> list[StatsRow]:
        """Build stats table rows from TimeStats.

        Args:
            stats: Statistics data.

        Returns:
            List of stats rows for the template.
        """
        rows: list[StatsRow] = []

        # Recent periods
        rows.append(StatsRow(Constants.PERIOD_LAST_7_DAYS, format_duration(stats.last_7_days)))
        rows.append(StatsRow(Constants.PERIOD_LAST_31_DAYS, format_duration(stats.last_31_days)))

        # Separator
        rows.append(StatsRow("", "", is_separator=True))

        # Averages
        rows.append(
            StatsRow(
                Constants.PERIOD_AVG_LAST_30_DAYS,
                format_duration(stats.avg_per_day_last_30_days),
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
                format_duration(stats.avg_per_day_last_12_months),
            )
        )
        rows.append(
            StatsRow(
                Constants.PERIOD_AVG_THIS_YEAR,
                format_duration(stats.avg_per_day_this_year),
            )
        )
        rows.append(
            StatsRow(
                Constants.PERIOD_AVG_LAST_YEAR,
                format_duration(stats.avg_per_day_last_year),
            )
        )

        # Separator
        rows.append(StatsRow("", "", is_separator=True))

        # Standard periods
        rows.append(StatsRow(Constants.PERIOD_THIS_WEEK, format_duration(stats.this_week)))
        rows.append(StatsRow(Constants.PERIOD_THIS_MONTH, format_duration(stats.this_month)))
        rows.append(StatsRow(Constants.PERIOD_LAST_MONTH, format_duration(stats.last_month)))
        rows.append(
            StatsRow(Constants.PERIOD_LAST_12_MONTHS, format_duration(stats.last_12_months))
        )
        rows.append(StatsRow(Constants.PERIOD_TOTAL, format_duration(stats.total)))

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
