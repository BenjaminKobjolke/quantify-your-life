"""Main entry point for the CLI application."""

import argparse
import sys
from pathlib import Path

from rich.console import Console

from quantify.cli.export_config_menu import ExportConfigMenu
from quantify.cli.menu import Menu
from quantify.cli.project_selector import ProjectSelector
from quantify.config.config_writer import ConfigWriter
from quantify.config.constants import Constants
from quantify.config.project_manager import ProjectManager
from quantify.config.settings import ConfigError, Settings
from quantify.export.html_exporter import HtmlExporter
from quantify.services.logger import get_logger
from quantify.sources.base import parse_display_config
from quantify.sources.excel import ExcelSource
from quantify.sources.git_stats import GitStatsSource
from quantify.sources.hometrainer import HometrainerSource
from quantify.sources.registry import SourceRegistry
from quantify.sources.track_and_graph import TrackAndGraphSource


def _create_source_registry(settings: Settings) -> SourceRegistry:
    """Create and populate source registry from settings.

    Args:
        settings: Application settings.

    Returns:
        SourceRegistry with all configured sources.
    """
    registry = SourceRegistry()

    # Register Track & Graph source
    if settings.sources.track_and_graph:
        tg_config = settings.sources.track_and_graph
        tg_source = TrackAndGraphSource(
            db_path=tg_config.db_path,
            display_config=parse_display_config(tg_config.display),
        )
        registry.register(tg_source)

    # Register Hometrainer source
    if settings.sources.hometrainer:
        ht_config = settings.sources.hometrainer
        ht_source = HometrainerSource(
            logs_path=ht_config.logs_path,
            unit=ht_config.unit,
            display_config=parse_display_config(ht_config.display),
        )
        registry.register(ht_source)

    # Register Git Stats source
    if settings.sources.git_stats:
        gs_config = settings.sources.git_stats
        gs_source = GitStatsSource(
            author=gs_config.author,
            root_paths=list(gs_config.root_paths),
            exclude_dirs=list(gs_config.exclude_dirs),
            exclude_extensions=list(gs_config.exclude_extensions),
            exclude_filenames=list(gs_config.exclude_filenames),
            display_config=parse_display_config(gs_config.display),
        )
        registry.register(gs_source)

    # Register Excel sources
    if settings.sources.excel:
        for idx, excel_src in enumerate(settings.sources.excel.sources):
            # Create unique source ID for each Excel source
            source_id = f"excel_{idx}" if idx > 0 else "excel"
            source = ExcelSource(
                source_id=source_id,
                name=excel_src.name,
                file_path=excel_src.file_path,
                tabs=excel_src.tabs,
                function=excel_src.function,
                unit_label=excel_src.unit_label,
                display_config=parse_display_config(excel_src.display),
            )
            registry.register(source)

    return registry


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Quantify Your Life - Statistics viewer and exporter"
    )
    parser.add_argument(
        "--project",
        "-p",
        type=str,
        help="Project name to use (from projects/ directory)",
    )
    parser.add_argument(
        "--list-projects",
        action="store_true",
        help="List all available projects and exit",
    )
    return parser.parse_args()


def _resolve_project_context(
    args: argparse.Namespace,
    console: Console,
) -> tuple[Path, Path | None] | None:
    """Resolve project and global config paths.

    Args:
        args: Parsed command-line arguments.
        console: Console for output.

    Returns:
        Tuple of (config_dir, global_config_path_or_none), or None to exit.
    """
    base_dir = Path.cwd()
    pm = ProjectManager(base_dir)

    # --list-projects: show and exit
    if args.list_projects:
        projects = pm.discover_projects()
        if not projects:
            console.print(f"[yellow]{Constants.PROJECT_NO_PROJECTS}[/yellow]")
        else:
            console.print("[bold]Available projects:[/bold]")
            for p in projects:
                status = "OK" if p.has_config else "missing config"
                console.print(f"  {p.name} ({status})")
        return None

    # --project specified
    if args.project:
        project_path = pm.get_project_path(args.project)
        if not project_path.exists():
            console.print(
                f"[red]{Constants.PROJECT_NOT_FOUND.format(name=args.project)}[/red]"
            )
            return None
        global_config = pm.get_global_config_path()
        return project_path, global_config if global_config.exists() else None

    # Check if projects exist for interactive selection
    if pm.projects_exist():
        selector = ProjectSelector(pm)
        selected = selector.select()

        if selected is None:
            # User chose Exit
            return None

        if selected == "":
            # User chose "Use root config.json"
            return base_dir, None

        project_path = pm.get_project_path(selected)
        global_config = pm.get_global_config_path()
        return project_path, global_config if global_config.exists() else None

    # No projects folder, use legacy behavior
    return base_dir, None


def _load_settings(
    config_dir: Path,
    global_config: Path | None,
    console: Console,
) -> Settings | None:
    """Load settings from resolved project context.

    Args:
        config_dir: Directory containing config.json.
        global_config: Optional path to global config for merging.
        console: Console for error output.

    Returns:
        Settings instance or None on error.
    """
    try:
        if global_config:
            return Settings.load_project(config_dir, global_config)
        else:
            return Settings.load(config_dir)
    except ConfigError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        return None


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    logger = get_logger()
    logger.info("Application started")
    console = Console()
    args = _parse_args()

    # Resolve project context
    context = _resolve_project_context(args, console)
    if context is None:
        return 0  # User chose to exit or list-projects was shown

    config_dir, global_config = context

    # Load settings
    settings = _load_settings(config_dir, global_config, console)
    if settings is None:
        return 1

    registry = _create_source_registry(settings)

    if not registry.get_configured_sources():
        console.print(f"[red]{Constants.SOURCE_NO_CONFIGURED}[/red]")
        return 1

    try:
        menu = Menu(registry)
        menu.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
    finally:
        registry.close_all()

    return 0


def export_config() -> int:
    """Entry point for export configuration CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    get_logger()  # Initialize logger to prevent console output
    console = Console()
    args = _parse_args()

    # Resolve project context
    context = _resolve_project_context(args, console)
    if context is None:
        return 0  # User chose to exit or list-projects was shown

    config_dir, global_config = context

    # Load settings
    settings = _load_settings(config_dir, global_config, console)
    if settings is None:
        return 1

    registry = _create_source_registry(settings)

    if not registry.get_configured_sources():
        console.print(f"[red]{Constants.SOURCE_NO_CONFIGURED}[/red]")
        return 1

    try:
        config_writer = ConfigWriter(
            config_dir / Constants.CONFIG_FILE_NAME,
            global_config,
        )
        menu = ExportConfigMenu(registry, config_writer)
        menu.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
    finally:
        registry.close_all()

    return 0


def export() -> int:
    """Entry point for HTML export CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    get_logger()  # Initialize logger to prevent console output
    console = Console()
    base_dir = Path.cwd()
    args = _parse_args()

    # Resolve project context
    context = _resolve_project_context(args, console)
    if context is None:
        return 0  # User chose to exit or list-projects was shown

    config_dir, global_config = context

    # Load settings
    settings = _load_settings(config_dir, global_config, console)
    if settings is None:
        return 1

    if settings.export is None:
        console.print(f"[yellow]{Constants.EXPORT_NO_ENTRIES}[/yellow]")
        return 1

    if not settings.export.path:
        console.print(f"[yellow]{Constants.EXPORT_NO_PATH}[/yellow]")
        return 1

    if not settings.export.entries:
        console.print(f"[yellow]{Constants.EXPORT_NO_ENTRIES}[/yellow]")
        return 1

    registry = _create_source_registry(settings)

    if not registry.get_configured_sources():
        console.print(f"[red]{Constants.SOURCE_NO_CONFIGURED}[/red]")
        return 1

    try:
        exporter = HtmlExporter(
            registry=registry,
            templates_dir=base_dir / "templates",
            static_dir=base_dir / "static",
        )

        generated_files = exporter.export(settings.export)
        msg = Constants.EXPORT_SUCCESS.format(
            count=len(generated_files), path=settings.export.path
        )
        console.print(f"[green]{msg}[/green]")

        # FTP sync if configured
        if settings.export.ftp_sync and settings.export.ftp_sync.enabled:
            from quantify.sync.ftp_syncer import FtpSyncer

            console.print("[cyan]Starting FTP sync...[/cyan]")
            try:
                syncer = FtpSyncer(settings.export.ftp_sync)
                syncer.sync(Path(settings.export.path))
                console.print("[green]FTP sync completed[/green]")
            except Exception as e:
                console.print(f"[red]FTP sync failed: {e}[/red]")
                return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
    finally:
        registry.close_all()

    return 0


if __name__ == "__main__":
    sys.exit(main())
