"""Main entry point for the CLI application."""

import sys
from pathlib import Path

from rich.console import Console

from quantify.cli.export_config_menu import ExportConfigMenu
from quantify.cli.menu import Menu
from quantify.config.config_writer import ConfigWriter
from quantify.config.constants import Constants
from quantify.config.settings import ConfigError, Settings
from quantify.db.connection import Database, DatabaseError
from quantify.db.repositories.datapoints import DataPointsRepository
from quantify.db.repositories.features import FeaturesRepository
from quantify.db.repositories.groups import GroupsRepository
from quantify.export.html_exporter import HtmlExporter
from quantify.services.stats import StatsService


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    console = Console()

    try:
        settings = Settings.load()
    except ConfigError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        return 1

    try:
        db = Database(settings.db_path)
    except DatabaseError as e:
        console.print(f"[red]Database error: {e}[/red]")
        return 1

    try:
        groups_repo = GroupsRepository(db)
        features_repo = FeaturesRepository(db)
        datapoints_repo = DataPointsRepository(db)
        stats_service = StatsService(datapoints_repo, features_repo)

        menu = Menu(groups_repo, features_repo, stats_service)
        menu.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
    finally:
        db.close()

    return 0


def export_config() -> int:
    """Entry point for export configuration CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    console = Console()
    base_dir = Path.cwd()

    try:
        settings = Settings.load(base_dir)
    except ConfigError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        return 1

    try:
        db = Database(settings.db_path)
    except DatabaseError as e:
        console.print(f"[red]Database error: {e}[/red]")
        return 1

    try:
        groups_repo = GroupsRepository(db)
        features_repo = FeaturesRepository(db)
        config_writer = ConfigWriter(base_dir / Constants.CONFIG_FILE_NAME)

        menu = ExportConfigMenu(groups_repo, features_repo, config_writer)
        menu.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
    finally:
        db.close()

    return 0


def export() -> int:
    """Entry point for HTML export CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
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

    if not settings.export.groups and not settings.export.features:
        console.print(f"[yellow]{Constants.EXPORT_NO_ENTRIES}[/yellow]")
        return 1

    try:
        db = Database(settings.db_path)
    except DatabaseError as e:
        console.print(f"[red]Database error: {e}[/red]")
        return 1

    try:
        groups_repo = GroupsRepository(db)
        features_repo = FeaturesRepository(db)
        datapoints_repo = DataPointsRepository(db)
        stats_service = StatsService(datapoints_repo, features_repo)

        exporter = HtmlExporter(
            stats_service=stats_service,
            groups_repo=groups_repo,
            features_repo=features_repo,
            templates_dir=base_dir / "templates",
            static_dir=base_dir / "static",
        )

        generated_files = exporter.export(settings.export)
        msg = Constants.EXPORT_SUCCESS.format(count=len(generated_files), path=settings.export.path)
        console.print(f"[green]{msg}[/green]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
