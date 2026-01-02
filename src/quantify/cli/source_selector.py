"""Reusable source selection component."""

from typing import cast

import questionary

from quantify.config.constants import Constants
from quantify.sources.base import DataSource
from quantify.sources.registry import SourceRegistry


class SourceSelector:
    """Reusable component for selecting a data source."""

    def __init__(self, registry: SourceRegistry) -> None:
        """Initialize selector.

        Args:
            registry: Source registry to select from.
        """
        self._registry = registry

    def select(self) -> DataSource | None:
        """Prompt user to select a configured data source.

        Only shows sources that are properly configured.

        Returns:
            Selected source or None if cancelled or no sources available.
        """
        sources = self._registry.get_configured_sources()

        if not sources:
            return None

        # If only one source, return it directly
        if len(sources) == 1:
            return sources[0]

        # Multiple sources - let user choose
        choices = [questionary.Choice(title=s.info.display_name, value=s) for s in sources]

        result = questionary.select(
            Constants.SOURCE_SELECT_TITLE,
            choices=choices,
        ).ask()

        return cast(DataSource | None, result)

    def has_configured_sources(self) -> bool:
        """Check if any sources are configured.

        Returns:
            True if at least one source is configured.
        """
        return len(self._registry.get_configured_sources()) > 0
