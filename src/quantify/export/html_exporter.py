"""HTML exporter for statistics."""

import shutil
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from quantify.cli.handlers.period_selector import get_period_label
from quantify.config.settings import ExportSettings
from quantify.export.monthly_builder import build_monthly_chart_data
from quantify.export.stats_builder import build_chart_data, build_stats_rows
from quantify.export.top_features_exporter import export_top_features
from quantify.services.monthly_stats import MonthlyStats
from quantify.services.stats import TimeStats
from quantify.sources.base import DisplayConfig
from quantify.sources.excel.source import ExcelSource
from quantify.sources.registry import SourceRegistry
from quantify.sources.track_and_graph import TrackAndGraphSource


class HtmlExporter:
    """Exports statistics to HTML files."""

    def __init__(
        self,
        registry: SourceRegistry,
        templates_dir: Path,
        static_dir: Path,
        php_login_lib_path: Path | None = None,
    ) -> None:
        """Initialize HTML exporter.

        Args:
            registry: Source registry with configured sources.
            templates_dir: Path to templates directory.
            static_dir: Path to static files directory.
            php_login_lib_path: Path to php-simple-login library (for PHP mode).
        """
        self._registry = registry
        self._templates_dir = templates_dir
        self._static_dir = static_dir
        self._php_login_lib_path = php_login_lib_path
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

        # Handle PHP mode setup
        php_mode = export_settings.php_mode
        if php_mode:
            if not export_settings.php_password:
                raise ValueError("php_password is required when php_mode is enabled")
            self._copy_php_library(output_dir)
            self._generate_php_config(output_dir, export_settings.php_password)

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
                    php_mode=php_mode,
                    php_wrapper_func=self._wrap_html_with_php if php_mode else None,
                )
                period_label = get_period_label(entry.period)
                display_name = f"Top Features - {group_name} ({period_label})"
                generated_files.append(file_path)
                index_entries.append({"name": display_name, "filename": file_path.name})
                continue

            # Handle monthly_comparison entry type
            if entry.entry_type == "monthly_comparison":
                if not isinstance(source, ExcelSource):
                    continue
                if not source.has_monthly_comparison:
                    continue

                monthly_stats = source.get_monthly_stats()
                if monthly_stats is None:
                    continue

                # Get item name for monthly comparison
                name = source.get_item_name(entry.entry_id, entry.entry_type)
                if name is None:
                    name = source.info.display_name

                file_path = self._export_monthly_comparison(
                    output_dir=output_dir,
                    name=name,
                    source_id=entry.source,
                    stats=monthly_stats,
                    custom_title=entry.title,
                    php_mode=php_mode,
                )
                generated_files.append(file_path)
                display_name = entry.title if entry.title else name
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

            # Export to HTML/PHP
            file_path = self._export_stats(
                output_dir=output_dir,
                name=name,
                entry_id=entry.entry_id,
                entry_type=entry.entry_type,
                source_id=entry.source,
                stats=stats,
                unit=unit,
                unit_label=unit_label,
                display_config=source.info.display_config,
                custom_title=entry.title,
                php_mode=php_mode,
            )
            generated_files.append(file_path)
            # Use custom title for index if provided
            display_name = entry.title if entry.title else name
            index_entries.append({"name": display_name, "filename": file_path.name})

        # Generate index page
        index_path = self._export_index(output_dir, index_entries, php_mode=php_mode)
        generated_files.insert(0, index_path)

        return generated_files

    def _export_index(
        self,
        output_dir: Path,
        entries: list[dict[str, str]],
        php_mode: bool = False,
    ) -> Path:
        """Generate index page with links to all exported stats.

        Args:
            output_dir: Output directory path.
            entries: List of dicts with 'name' and 'filename' keys.
            php_mode: If True, output PHP file with authentication.

        Returns:
            Path to generated index file.
        """
        template = self._env.get_template("index.html")

        html_content = template.render(
            entries=entries,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

        extension = ".php" if php_mode else ".html"
        file_path = output_dir / f"index{extension}"

        # Wrap with PHP authentication if enabled
        content = self._wrap_html_with_php(html_content) if php_mode else html_content

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

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

        src_monthly_js = self._static_dir / "js" / "monthly_chart.js"
        if src_monthly_js.exists():
            shutil.copy(src_monthly_js, js_dir / "monthly_chart.js")

    def _copy_php_library(self, output_dir: Path) -> None:
        """Copy php-simple-login source files to output directory.

        Args:
            output_dir: Output directory path.
        """
        if self._php_login_lib_path is None:
            return

        lib_dir = output_dir / "lib" / "simple-login"
        lib_dir.mkdir(parents=True, exist_ok=True)

        for filename in ("SimpleLogin.php", "Session.php"):
            src = self._php_login_lib_path / "src" / filename
            if src.exists():
                shutil.copy(src, lib_dir / filename)

    def _generate_php_config(self, output_dir: Path, password: str) -> None:
        """Generate simple-login-config.php with password.

        Args:
            output_dir: Output directory path.
            password: Login password.
        """
        content = f"""<?php
/**
 * Simple Login Configuration
 * Auto-generated by Quantify Your Life
 */

define('SIMPLE_LOGIN_PASSWORD', '{password}');
"""
        config_path = output_dir / "simple-login-config.php"
        config_path.write_text(content, encoding="utf-8")

    def _wrap_html_with_php(self, html_content: str) -> str:
        """Wrap HTML content with PHP authentication code.

        Args:
            html_content: Original HTML content.

        Returns:
            PHP file content with authentication.
        """
        php_header = """<?php
// Load config first (defines SIMPLE_LOGIN_PASSWORD constant)
require_once __DIR__ . '/simple-login-config.php';

// Load library files
require_once __DIR__ . '/lib/simple-login/Session.php';
require_once __DIR__ . '/lib/simple-login/SimpleLogin.php';

use BenjaminKobjolke\\SimpleLogin\\SimpleLogin;

SimpleLogin::requireAuth();
?>
"""
        return php_header + html_content

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
        display_config: DisplayConfig | None = None,
        custom_title: str | None = None,
        php_mode: bool = False,
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
            display_config: Optional display configuration for filtering rows.
            custom_title: Optional custom page title (uses name if None).
            php_mode: If True, output PHP file with authentication.

        Returns:
            Path to generated file.
        """
        template = self._env.get_template("stats.html")

        title = custom_title if custom_title else name
        stats_rows = build_stats_rows(stats, unit, unit_label, display_config)
        chart_labels, chart_values = build_chart_data(stats, display_config)

        # Build chart title
        chart_title = None
        if display_config and display_config.chart:
            chart_title = display_config.chart.title
        if not chart_title:
            # Generate default title based on chart type
            if display_config and display_config.chart:
                chart_type = display_config.chart.chart_type
            else:
                chart_type = "periods"
            if chart_type == "yearly":
                chart_title = f"{unit_label.capitalize()} by Year"
            else:
                chart_title = f"{unit_label.capitalize()} by Period"

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
            chart_title=chart_title,
            unit=unit,
            unit_label=unit_label,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

        # Generate filename with appropriate extension
        extension = ".php" if php_mode else ".html"
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        entry_id_str = str(entry_id) if entry_id is not None else "all"
        filename = f"{source_id}_{entry_type}_{entry_id_str}_{safe_name}{extension}"
        file_path = output_dir / filename

        # Wrap with PHP authentication if enabled
        content = self._wrap_html_with_php(html_content) if php_mode else html_content

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return file_path

    def _export_monthly_comparison(
        self,
        output_dir: Path,
        name: str,
        source_id: str,
        stats: MonthlyStats,
        custom_title: str | None = None,
        php_mode: bool = False,
    ) -> Path:
        """Export monthly comparison chart for an Excel source.

        Args:
            output_dir: Output directory path.
            name: Name of the item.
            source_id: Source identifier.
            stats: Monthly comparison statistics.
            custom_title: Optional custom page title (uses name if None).
            php_mode: If True, output PHP file with authentication.

        Returns:
            Path to generated file.
        """
        template = self._env.get_template("monthly_comparison.html")

        title = custom_title if custom_title else name
        chart_data = build_monthly_chart_data(stats)

        # Build chart title
        unit_label = stats.unit_label or "Value"
        chart_title = f"Monthly {unit_label.capitalize()} by Year"

        html_content = template.render(
            title=title,
            chart_labels=chart_data["labels"],
            chart_datasets=chart_data["datasets"],
            chart_title=chart_title,
            unit_label=stats.unit_label,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

        # Generate filename with appropriate extension
        extension = ".php" if php_mode else ".html"
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        filename = f"{source_id}_monthly_comparison_all_{safe_name}{extension}"
        file_path = output_dir / filename

        # Wrap with PHP authentication if enabled
        content = self._wrap_html_with_php(html_content) if php_mode else html_content

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return file_path
