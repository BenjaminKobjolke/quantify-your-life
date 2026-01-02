"""Main entry point for the CLI application."""

import sys
from pathlib import Path

from rich.console import Console

from quantify.cli.export_config_menu import ExportConfigMenu
from quantify.cli.menu import Menu
from quantify.config.config_writer import ConfigWriter
from quantify.config.constants import Constants
from quantify.config.settings import ConfigError, Settings
from quantify.export.html_exporter import HtmlExporter
from quantify.services.logger import get_logger
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
        tg_source = TrackAndGraphSource(settings.sources.track_and_graph.db_path)
        registry.register(tg_source)

    # Register Hometrainer source
    if settings.sources.hometrainer:
        ht_source = HometrainerSource(
            settings.sources.hometrainer.logs_path,
            settings.sources.hometrainer.unit,
        )
        registry.register(ht_source)

    # Register Git Stats source
    if settings.sources.git_stats:
        gs_source = GitStatsSource(
            author=settings.sources.git_stats.author,
            root_paths=list(settings.sources.git_stats.root_paths),
            exclude_dirs=list(settings.sources.git_stats.exclude_dirs),
            exclude_extensions=list(settings.sources.git_stats.exclude_extensions),
            exclude_filenames=list(settings.sources.git_stats.exclude_filenames),
        )
        registry.register(gs_source)

    return registry


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    logger = get_logger()
    logger.info("Application started")
    console = Console()

    try:
        settings = Settings.load()
    except ConfigError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
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
    base_dir = Path.cwd()

    try:
        settings = Settings.load(base_dir)
    except ConfigError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        return 1

    registry = _create_source_registry(settings)

    if not registry.get_configured_sources():
        console.print(f"[red]{Constants.SOURCE_NO_CONFIGURED}[/red]")
        return 1

    try:
        config_writer = ConfigWriter(base_dir / Constants.CONFIG_FILE_NAME)
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

    try:
        settings = Settings.load(base_dir)
    except ConfigError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
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
