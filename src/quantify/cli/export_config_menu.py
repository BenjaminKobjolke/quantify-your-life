"""Interactive CLI menu for configuring HTML export."""

import re
import sys
from dataclasses import dataclass
from typing import cast

import questionary
from rich.console import Console

from quantify.config.config_writer import ConfigWriter
from quantify.config.constants import Constants
from quantify.db.repositories.features import Feature, FeaturesRepository
from quantify.db.repositories.groups import Group, GroupsRepository


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

    entry_type: str  # "group" or "feature"
    id: int
    name: str


class ExportConfigMenu:
    """Interactive CLI menu for managing export configuration."""

    def __init__(
        self,
        groups_repo: GroupsRepository,
        features_repo: FeaturesRepository,
        config_writer: ConfigWriter,
    ) -> None:
        """Initialize export config menu.

        Args:
            groups_repo: Repository for groups.
            features_repo: Repository for features.
            config_writer: Writer for config file.
        """
        self._groups = groups_repo
        self._features = features_repo
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
        entry_type = self._ask_entry_type()
        if entry_type is None:
            return

        if entry_type == Constants.EXPORT_TYPE_GROUP:
            self._add_group()
        else:
            self._add_feature()

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

    def _add_group(self) -> None:
        """Add a group to export config."""
        groups = self._groups.get_all()
        if not groups:
            self._console.print(f"[red]{Constants.ERROR_NO_GROUPS}[/red]")
            return

        selected = self._select_group(groups)
        if selected is None:
            return

        if self._config_writer.add_export_group(selected.id):
            msg = Constants.EXPORT_ADDED_GROUP.format(name=selected.name, id=selected.id)
            self._console.print(f"[green]{msg}[/green]")
        else:
            msg = Constants.EXPORT_ALREADY_EXISTS.format(name=selected.name)
            self._console.print(f"[yellow]{msg}[/yellow]")

    def _select_group(self, groups: list[Group]) -> Group | None:
        """Let user select a group.

        Args:
            groups: List of available groups.

        Returns:
            Selected group or None if cancelled.
        """
        choices = [questionary.Choice(title=g.name, value=g) for g in groups]
        result = questionary.select(
            Constants.EXPORT_SELECT_GROUP,
            choices=choices,
        ).ask()
        return cast(Group | None, result)

    def _add_feature(self) -> None:
        """Add a feature to export config."""
        features = self._features.get_all()
        if not features:
            self._console.print(f"[red]{Constants.ERROR_NO_FEATURES}[/red]")
            return

        selected = self._select_feature(features)
        if selected is None:
            return

        if self._config_writer.add_export_feature(selected.id):
            msg = Constants.EXPORT_ADDED_FEATURE.format(name=selected.name, id=selected.id)
            self._console.print(f"[green]{msg}[/green]")
        else:
            msg = Constants.EXPORT_ALREADY_EXISTS.format(name=selected.name)
            self._console.print(f"[yellow]{msg}[/yellow]")

    def _select_feature(self, features: list[Feature]) -> Feature | None:
        """Let user select a feature.

        Args:
            features: List of available features.

        Returns:
            Selected feature or None if cancelled.
        """
        choices = [questionary.Choice(title=f.name, value=f) for f in features]
        result = questionary.select(
            Constants.EXPORT_SELECT_FEATURE,
            choices=choices,
        ).ask()
        return cast(Feature | None, result)

    def _handle_remove(self) -> None:
        """Handle removing an entry from export config."""
        entries = self._get_configured_entries()
        if not entries:
            self._console.print(f"[yellow]{Constants.EXPORT_NO_ENTRIES}[/yellow]")
            return

        selected = self._select_entry_to_remove(entries)
        if selected is None:
            return

        if selected.entry_type == "group":
            self._config_writer.remove_export_group(selected.id)
        else:
            self._config_writer.remove_export_feature(selected.id)

        self._console.print(f"[green]{Constants.EXPORT_REMOVED.format(name=selected.name)}[/green]")

    def _get_configured_entries(self) -> list[ExportEntry]:
        """Get all configured export entries with names.

        Returns:
            List of export entries.
        """
        entries: list[ExportEntry] = []

        for group_id in self._config_writer.get_export_groups():
            group = self._groups.get_by_id(group_id)
            if group:
                entries.append(ExportEntry("group", group.id, group.name))

        for feature_id in self._config_writer.get_export_features():
            feature = self._features.get_by_id(feature_id)
            if feature:
                entries.append(ExportEntry("feature", feature.id, feature.name))

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
            if entry.entry_type == "group":
                title = Constants.EXPORT_LABEL_GROUP.format(name=entry.name, id=entry.id)
            else:
                title = Constants.EXPORT_LABEL_FEATURE.format(name=entry.name, id=entry.id)
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
