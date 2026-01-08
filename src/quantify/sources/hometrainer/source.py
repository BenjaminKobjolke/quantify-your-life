"""Hometrainer data source implementation."""

from pathlib import Path

from quantify.services.stats_calculator import StatsCalculator, TimeStats
from quantify.sources.base import (
    DataProvider,
    DataSource,
    DisplayConfig,
    SelectableItem,
    SourceInfo,
)
from quantify.sources.hometrainer.data_provider import HometrainerDataProvider
from quantify.sources.hometrainer.log_reader import HometrainerLogReader


class HometrainerSource(DataSource):
    """Data source for Hometrainer log files."""

    def __init__(
        self,
        logs_path: str | None,
        unit: str = "km",
        display_config: DisplayConfig | None = None,
    ) -> None:
        """Initialize Hometrainer source.

        Args:
            logs_path: Path to the Hometrainer_Logs directory.
            unit: Display unit - "km" or "mi". Default is "km".
            display_config: Optional display configuration for stats output.
        """
        self._logs_path = logs_path
        self._unit = unit
        self._display_config = display_config or DisplayConfig()
        self._log_reader: HometrainerLogReader | None = None

    @property
    def info(self) -> SourceInfo:
        """Return metadata about this source."""
        return SourceInfo(
            id="hometrainer",
            display_name="Hometrainer",
            unit="distance",
            unit_label=self._unit,
            display_config=self._display_config,
        )

    def is_configured(self) -> bool:
        """Return True if logs path is set and directory exists."""
        if not self._logs_path:
            return False
        return Path(self._logs_path).exists()

    def _ensure_reader(self) -> None:
        """Ensure log reader is initialized."""
        if self._log_reader is None:
            if not self._logs_path:
                raise RuntimeError("Hometrainer source not configured")
            self._log_reader = HometrainerLogReader(Path(self._logs_path))

    def get_selectable_items(self) -> list[SelectableItem]:
        """Return single stats item for Hometrainer.

        Unlike Track & Graph, Hometrainer has no groups/features.
        It provides a single aggregated statistics view.
        """
        label = f"Hometrainer ({self._unit})"
        return [SelectableItem(None, label, "stats")]

    def get_item_name(self, item_id: int | None, item_type: str) -> str | None:
        """Get the name of an item.

        For Hometrainer, there's only one item.

        Args:
            item_id: Ignored for Hometrainer.
            item_type: Should be "stats".

        Returns:
            The item name.
        """
        if item_type == "stats":
            return f"Hometrainer ({self._unit})"
        return None

    def get_data_provider(
        self, item_id: int | None = None, item_type: str | None = None
    ) -> DataProvider:
        """Get the data provider for Hometrainer.

        Args:
            item_id: Ignored (Hometrainer has single stats).
            item_type: Ignored (always returns same provider).

        Returns:
            DataProvider for calculating sums.
        """
        self._ensure_reader()
        assert self._log_reader is not None
        return HometrainerDataProvider(self._log_reader, self._unit)

    def get_stats(
        self, item_id: int | None = None, item_type: str | None = None
    ) -> TimeStats:
        """Calculate statistics for Hometrainer.

        Args:
            item_id: Ignored (Hometrainer has single stats).
            item_type: Ignored (always calculates same stats).

        Returns:
            TimeStats with all calculated periods.
        """
        provider = self.get_data_provider(item_id, item_type)
        calculator = StatsCalculator()
        return calculator.calculate(provider.get_sum, self._display_config.show_years)

    def close(self) -> None:
        """Close resources (no-op for file-based source)."""
        self._log_reader = None
