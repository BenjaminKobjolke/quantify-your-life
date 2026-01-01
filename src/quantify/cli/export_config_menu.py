"""Interactive CLI menu for configuring HTML export."""

import re
import sys
from dataclasses import dataclass
from typing import cast

import questionary
from rich.console import Console

from quantify.config.config_writer import ConfigWriter
from quantify.config.constants import Constants
from quantify.sources.base import DataSource, SelectableItem
from quantify.sources.hometrainer import HometrainerSource
from quantify.sources.registry import SourceRegistry
from quantify.sources.track_and_graph import TrackAndGraphSource


def _normalize_path(path: str) -> str:
    """Normalize path for the current OS.

    Converts WSL-style paths (/mnt/d/...) to Windows paths on Windows.

    Args:
        path: Input path string.

    Returns:
        Normalized path string.
    """
    if sys.platform == "win32":
        # Convert WSL path /mnt/d/... to D:\...
        match = re.match(r"^/mnt/([a-zA-Z])/(.*)$", path)
        if match:
            drive = match.group(1).upper()
            rest = match.group(2).replace("/", "\\")
            return f"{drive}:\\{rest}"
    return path


@dataclass
class ExportEntry:
    """Represents a configured export entry."""

    source: str
    entry_type: str  # "group", "feature", "stats"
    entry_id: int | None
    name: str


class ExportConfigMenu:
    """Interactive CLI menu for managing export configuration."""

    def __init__(
        self,
        registry: SourceRegistry,
        config_writer: ConfigWriter,
    ) -> None:
        """Initialize export config menu.

        Args:
            registry: Source registry with configured sources.
            config_writer: Writer for config file.
        """
        self._registry = registry
        self._config_writer = config_writer
        self._console = Console()

    def run(self) -> None:
        """Run the interactive export config menu."""
        while True:
            action = self._ask_action()
            if action is None or action == Constants.EXPORT_MENU_EXIT:
                break

            if action == Constants.EXPORT_MENU_ADD:
                self._handle_add()
            elif action == Constants.EXPORT_MENU_REMOVE:
                self._handle_remove()
            elif action == Constants.EXPORT_MENU_SET_PATH:
                self._handle_set_path()

    def _ask_action(self) -> str | None:
        """Ask user what action to take.

        Returns:
            Selected action or None if cancelled.
        """
        result = questionary.select(
            Constants.EXPORT_MENU_TITLE,
            choices=[
                Constants.EXPORT_MENU_ADD,
                Constants.EXPORT_MENU_REMOVE,
                Constants.EXPORT_MENU_SET_PATH,
                Constants.EXPORT_MENU_EXIT,
            ],
        ).ask()
        return cast(str | None, result)

    def _handle_add(self) -> None:
        """Handle adding an entry to export config."""
        # Select source first
        sources = self._registry.get_configured_sources()
        if not sources:
            self._console.print(f"[red]{Constants.SOURCE_NO_CONFIGURED}[/red]")
            return

        source = self._select_source(sources)
        if source is None:
            return

        # Handle source-specific add flow
        if isinstance(source, TrackAndGraphSource):
            self._add_track_and_graph_entry(source)
        elif isinstance(source, HometrainerSource):
            self._add_hometrainer_entry(source)
        else:
            self._add_generic_entry(source)

    def _select_source(self, sources: list[DataSource]) -> DataSource | None:
        """Select a data source.

        Args:
            sources: List of configured sources.

        Returns:
            Selected source or None if cancelled.
        """
        if len(sources) == 1:
            return sources[0]

        choices = [
            questionary.Choice(title=s.info.display_name, value=s) for s in sources
        ]

        result = questionary.select(
            Constants.SOURCE_SELECT_TITLE,
            choices=choices,
        ).ask()

        return cast(DataSource | None, result)

    def _add_track_and_graph_entry(self, source: TrackAndGraphSource) -> None:
        """Add a Track & Graph entry."""
        entry_type = self._ask_entry_type()
        if entry_type is None:
            return

        if entry_type == Constants.EXPORT_TYPE_GROUP:
            items = source.get_groups()
            if not items:
                self._console.print(f"[red]{Constants.ERROR_NO_GROUPS}[/red]")
                return

            selected = self._select_item(items, Constants.EXPORT_SELECT_GROUP)
            if selected is None:
                return

            if self._config_writer.add_export_entry(
                source.info.id, "group", selected.id
            ):
                msg = Constants.EXPORT_ADDED_GROUP.format(
                    name=selected.name, id=selected.id
                )
                self._console.print(f"[green]{msg}[/green]")
            else:
                msg = Constants.EXPORT_ALREADY_EXISTS.format(name=selected.name)
                self._console.print(f"[yellow]{msg}[/yellow]")
        else:
            items = source.get_features()
            if not items:
                self._console.print(f"[red]{Constants.ERROR_NO_FEATURES}[/red]")
                return

            selected = self._select_item(items, Constants.EXPORT_SELECT_FEATURE)
            if selected is None:
                return

            if self._config_writer.add_export_entry(
                source.info.id, "feature", selected.id
            ):
                msg = Constants.EXPORT_ADDED_FEATURE.format(
                    name=selected.name, id=selected.id
                )
                self._console.print(f"[green]{msg}[/green]")
            else:
                msg = Constants.EXPORT_ALREADY_EXISTS.format(name=selected.name)
                self._console.print(f"[yellow]{msg}[/yellow]")

    def _add_hometrainer_entry(self, source: HometrainerSource) -> None:
        """Add a Hometrainer entry."""
        items = source.get_selectable_items()
        if not items:
            return

        item = items[0]
        if self._config_writer.add_export_entry(source.info.id, "stats", None):
            self._console.print(
                f"[green]Added {item.name} to export config[/green]"
            )
        else:
            msg = Constants.EXPORT_ALREADY_EXISTS.format(name=item.name)
            self._console.print(f"[yellow]{msg}[/yellow]")

    def _add_generic_entry(self, source: DataSource) -> None:
        """Add an entry from a generic source."""
        items = source.get_selectable_items()
        if not items:
            self._console.print("[yellow]No items available[/yellow]")
            return

        if len(items) == 1:
            item = items[0]
        else:
            item = self._select_item(items, "Select item:")
            if item is None:
                return

        if self._config_writer.add_export_entry(
            source.info.id, item.item_type, item.id
        ):
            self._console.print(f"[green]Added {item.name} to export config[/green]")
        else:
            msg = Constants.EXPORT_ALREADY_EXISTS.format(name=item.name)
            self._console.print(f"[yellow]{msg}[/yellow]")

    def _ask_entry_type(self) -> str | None:
        """Ask user what type of entry to add.

        Returns:
            Selected type or None if cancelled.
        """
        result = questionary.select(
            Constants.EXPORT_TYPE_TITLE,
            choices=[Constants.EXPORT_TYPE_GROUP, Constants.EXPORT_TYPE_FEATURE],
        ).ask()
        return cast(str | None, result)

    def _select_item(
        self, items: list[SelectableItem], prompt: str
    ) -> SelectableItem | None:
        """Let user select an item.

        Args:
            items: List of available items.
            prompt: Prompt text.

        Returns:
            Selected item or None if cancelled.
        """
        choices = [questionary.Choice(title=item.name, value=item) for item in items]
        result = questionary.select(prompt, choices=choices).ask()
        return cast(SelectableItem | None, result)

    def _handle_remove(self) -> None:
        """Handle removing an entry from export config."""
        entries = self._get_configured_entries()
        if not entries:
            self._console.print(f"[yellow]{Constants.EXPORT_NO_ENTRIES}[/yellow]")
            return

        selected = self._select_entry_to_remove(entries)
        if selected is None:
            return

        self._config_writer.remove_export_entry(
            selected.source, selected.entry_type, selected.entry_id
        )
        self._console.print(
            f"[green]{Constants.EXPORT_REMOVED.format(name=selected.name)}[/green]"
        )

    def _get_configured_entries(self) -> list[ExportEntry]:
        """Get all configured export entries with names.

        Returns:
            List of export entries.
        """
        entries: list[ExportEntry] = []

        for entry_data in self._config_writer.get_export_entries():
            source = self._registry.get_by_id(entry_data.source)
            if source is None:
                # Source not configured, use raw data
                name = f"{entry_data.source}: {entry_data.entry_type} {entry_data.entry_id}"
                entries.append(
                    ExportEntry(
                        entry_data.source,
                        entry_data.entry_type,
                        entry_data.entry_id,
                        name,
                    )
                )
                continue

            # Get item name from source
            if isinstance(source, (TrackAndGraphSource, HometrainerSource)):
                item_name = source.get_item_name(entry_data.entry_id, entry_data.entry_type)
                if item_name:
                    entries.append(
                        ExportEntry(
                            entry_data.source,
                            entry_data.entry_type,
                            entry_data.entry_id,
                            item_name,
                        )
                    )

        return entries

    def _select_entry_to_remove(self, entries: list[ExportEntry]) -> ExportEntry | None:
        """Let user select an entry to remove.

        Args:
            entries: List of configured entries.

        Returns:
            Selected entry or None if cancelled.
        """
        choices = []
        for entry in entries:
            source = self._registry.get_by_id(entry.source)
            source_name = source.info.display_name if source else entry.source

            if entry.entry_type == "group":
                title = Constants.EXPORT_LABEL_GROUP.format(
                    name=entry.name, id=entry.entry_id
                )
            elif entry.entry_type == "feature":
                title = Constants.EXPORT_LABEL_FEATURE.format(
                    name=entry.name, id=entry.entry_id
                )
            else:
                title = Constants.EXPORT_LABEL_STATS.format(
                    source=source_name, name=entry.name
                )

            choices.append(questionary.Choice(title=title, value=entry))

        result = questionary.select(
            Constants.EXPORT_SELECT_REMOVE,
            choices=choices,
        ).ask()
        return cast(ExportEntry | None, result)

    def _handle_set_path(self) -> None:
        """Handle setting the export path."""
        current_path = self._config_writer.get_export_path()
        path = questionary.text(
            Constants.EXPORT_ENTER_PATH,
            default=current_path,
        ).ask()

        if path is not None and path.strip():
            normalized_path = _normalize_path(path.strip())
            self._config_writer.set_export_path(normalized_path)
            self._console.print(
                f"[green]{Constants.EXPORT_PATH_SET.format(path=normalized_path)}[/green]"
            )
