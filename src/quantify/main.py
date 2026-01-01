"""Main entry point for the CLI application."""

import sys

from rich.console import Console

from quantify.cli.menu import Menu
from quantify.config.settings import ConfigError, Settings
from quantify.db.connection import Database, DatabaseError
from quantify.db.repositories.datapoints import DataPointsRepository
from quantify.db.repositories.features import FeaturesRepository
from quantify.db.repositories.groups import GroupsRepository
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


if __name__ == "__main__":
    sys.exit(main())
