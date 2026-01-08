"""Base classes and protocols for data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol

from quantify.services.stats_calculator import TimeStats


@dataclass(frozen=True)
class ChartConfig:
    """Chart configuration for HTML export."""

    chart_type: str = "periods"  # "periods" or "yearly"
    title: str | None = None  # Custom chart title (auto-generated if None)


@dataclass(frozen=True)
class DisplayConfig:
    """Display configuration for stats output."""

    hide_rows: tuple[str, ...] = ()
    show_rows: tuple[str, ...] = ()
    show_years: int = 3  # Number of years to display (default: 3)
    show_all_yoy: bool = False  # Show YoY percentage after every year
    chart: ChartConfig = field(default_factory=ChartConfig)


def parse_chart_config(config_dict: dict[str, Any] | None) -> ChartConfig:
    """Parse chart configuration from a config dictionary.

    Args:
        config_dict: Dictionary with 'type' and/or 'title' keys.

    Returns:
        ChartConfig instance.
    """
    if not config_dict:
        return ChartConfig()
    return ChartConfig(
        chart_type=config_dict.get("type", "periods"),
        title=config_dict.get("title"),
    )


def parse_display_config(config_dict: dict[str, Any] | None) -> DisplayConfig:
    """Parse display configuration from a config dictionary.

    Args:
        config_dict: Dictionary with 'hide_rows', 'show_rows', 'show_years',
                     'show_all_yoy', and/or 'chart' keys.

    Returns:
        DisplayConfig instance.
    """
    if not config_dict:
        return DisplayConfig()
    return DisplayConfig(
        hide_rows=tuple(config_dict.get("hide_rows", [])),
        show_rows=tuple(config_dict.get("show_rows", [])),
        show_years=config_dict.get("show_years", 3),
        show_all_yoy=config_dict.get("show_all_yoy", False),
        chart=parse_chart_config(config_dict.get("chart")),
    )


@dataclass(frozen=True)
class SourceInfo:
    """Metadata about a data source."""

    id: str  # e.g., "track_and_graph", "hometrainer"
    display_name: str  # e.g., "Track & Graph", "Hometrainer"
    unit: str  # e.g., "time" (seconds), "distance" (miles/km)
    unit_label: str  # e.g., "h", "km", "mi"
    display_config: DisplayConfig = field(default_factory=DisplayConfig)


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
