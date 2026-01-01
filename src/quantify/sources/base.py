"""Base classes and protocols for data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from quantify.services.stats_calculator import TimeStats


@dataclass(frozen=True)
class SourceInfo:
    """Metadata about a data source."""

    id: str  # e.g., "track_and_graph", "hometrainer"
    display_name: str  # e.g., "Track & Graph", "Hometrainer"
    unit: str  # e.g., "time" (seconds), "distance" (miles/km)
    unit_label: str  # e.g., "h", "km", "mi"


@dataclass(frozen=True)
class SelectableItem:
    """An item that can be selected for viewing/export."""

    id: int | None  # None for single-stat sources like Hometrainer
    name: str
    item_type: str  # "group", "feature", "stats"


class DataProvider(Protocol):
    """Protocol for providing aggregated data for statistics calculation.

    Each source implements this to provide data from their storage format.
    The StatsCalculator uses this protocol to calculate all time periods.
    """

    def get_sum(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> float:
        """Return sum of values in date range (inclusive).

        Args:
            start_date: First day to include (None for no lower bound).
            end_date: Last day to include (None for today).

        Returns:
            Sum of values (e.g., seconds for time, miles for distance).
        """
        ...


class DataSource(ABC):
    """Abstract base class for all data sources.

    Implementations:
    - TrackAndGraphSource: SQLite database with groups/features
    - HometrainerSource: Log files with daily distance values
    """

    @property
    @abstractmethod
    def info(self) -> SourceInfo:
        """Return metadata about this data source."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if this source is properly configured and accessible."""
        ...

    @abstractmethod
    def get_selectable_items(self) -> list[SelectableItem]:
        """Return items that can be selected for viewing/export.

        For Track & Graph: groups and features.
        For Hometrainer: single "Hometrainer" stats item.
        """
        ...

    @abstractmethod
    def get_item_name(
        self, item_id: int | None, item_type: str
    ) -> str | None:
        """Get the name of an item by ID and type.

        Args:
            item_id: The item ID (None for sources with single stats).
            item_type: "group", "feature", or "stats".

        Returns:
            The item name, or None if not found.
        """
        ...

    @abstractmethod
    def get_data_provider(
        self, item_id: int | None = None, item_type: str | None = None
    ) -> DataProvider:
        """Get a data provider for the specified item.

        Args:
            item_id: ID of the item (None for sources with single stats).
            item_type: Type of item ("group", "feature", "stats").

        Returns:
            DataProvider that can calculate sums for date ranges.
        """
        ...

    @abstractmethod
    def get_stats(
        self, item_id: int | None = None, item_type: str | None = None
    ) -> TimeStats:
        """Calculate statistics for the specified item.

        This is a convenience method that creates a data provider and
        uses StatsCalculator to compute all time periods.

        Args:
            item_id: ID of the item (None for sources with single stats).
            item_type: Type of item ("group", "feature", "stats").

        Returns:
            TimeStats with all calculated periods.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Close any resources held by this source."""
        ...
