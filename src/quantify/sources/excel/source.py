"""Excel data source implementation."""

from pathlib import Path

from quantify.services.stats_calculator import StatsCalculator, TimeStats
from quantify.sources.base import (
    DataProvider,
    DataSource,
    DisplayConfig,
    SelectableItem,
    SourceInfo,
)
from quantify.sources.excel.data_provider import ExcelDataProvider
from quantify.sources.excel.reader import ExcelReader


class ExcelSource(DataSource):
    """Data source for Excel files with yearly tab structure.

    Each instance represents a single Excel source configuration
    (one file with tabs representing years).
    """

    def __init__(
        self,
        source_id: str,
        name: str,
        file_path: str,
        tabs: dict[str, str],  # {tab_name: column_range}
        function: str = "sum",
        unit_label: str = "",
        display_config: DisplayConfig | None = None,
    ) -> None:
        """Initialize Excel source.

        Args:
            source_id: Unique identifier for this source.
            name: Display name for the source.
            file_path: Path to the Excel file.
            tabs: Dict mapping tab names (years) to column ranges.
            function: Aggregation function (currently only "sum").
            unit_label: Unit label for display.
            display_config: Optional display configuration for stats output.
        """
        self._source_id = source_id
        self._name = name
        self._file_path = file_path
        self._tabs = tabs
        self._function = function
        self._unit_label = unit_label
        self._display_config = display_config or DisplayConfig()
        self._reader: ExcelReader | None = None

    @property
    def info(self) -> SourceInfo:
        """Return metadata about this source."""
        return SourceInfo(
            id=self._source_id,
            display_name=self._name,
            unit="value",  # Generic for Excel values
            unit_label=self._unit_label,
            display_config=self._display_config,
        )

    def is_configured(self) -> bool:
        """Return True if Excel file exists and has required tabs."""
        path = Path(self._file_path)
        return path.exists()

    def _ensure_reader(self) -> ExcelReader:
        """Ensure reader is initialized and return it."""
        if self._reader is None:
            self._reader = ExcelReader(Path(self._file_path))
        return self._reader

    def get_selectable_items(self) -> list[SelectableItem]:
        """Return single stats item for this Excel source."""
        label = self._name
        if self._unit_label:
            label = f"{self._name} ({self._unit_label})"
        return [SelectableItem(None, label, "stats")]

    def get_item_name(self, item_id: int | None, item_type: str) -> str | None:
        """Get the name of an item.

        Args:
            item_id: Ignored for Excel sources.
            item_type: Should be "stats".

        Returns:
            The item name.
        """
        if item_type == "stats":
            label = self._name
            if self._unit_label:
                label = f"{self._name} ({self._unit_label})"
            return label
        return None

    def get_data_provider(
        self, item_id: int | None = None, item_type: str | None = None
    ) -> DataProvider:
        """Get the data provider for this Excel source.

        Args:
            item_id: Ignored (Excel has single stats per source).
            item_type: Ignored (always returns same provider).

        Returns:
            DataProvider for calculating sums.
        """
        reader = self._ensure_reader()
        return ExcelDataProvider(reader, self._tabs)

    def get_stats(
        self, item_id: int | None = None, item_type: str | None = None
    ) -> TimeStats:
        """Calculate statistics for this Excel source.

        Args:
            item_id: Ignored (Excel has single stats per source).
            item_type: Ignored (always calculates same stats).

        Returns:
            TimeStats with all calculated periods.
        """
        provider = self.get_data_provider(item_id, item_type)
        calculator = StatsCalculator()
        return calculator.calculate(provider.get_sum, self._display_config.show_years)

    def close(self) -> None:
        """Close resources."""
        if self._reader is not None:
            self._reader.close()
            self._reader = None
