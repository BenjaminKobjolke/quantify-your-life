"""Excel data source implementation."""

from pathlib import Path

from quantify.services.monthly_stats import MonthlyStats
from quantify.services.okr_stats import OkrStats
from quantify.services.stats_calculator import StatsCalculator, TimeStats
from quantify.sources.base import (
    DataProvider,
    DataSource,
    DisplayConfig,
    SelectableItem,
    SourceInfo,
)
from quantify.sources.excel.data_provider import ExcelDataProvider, MonthlyDataProvider
from quantify.sources.excel.reader import ExcelReader


class ExcelSource(DataSource):
    """Data source for Excel files with yearly tab structure.

    Each instance represents a single Excel source configuration
    (one file with tabs representing years, or OKR tabs).
    """

    def __init__(
        self,
        source_id: str,
        name: str,
        file_path: str,
        tabs: dict[str, str] | list[str],
        function: str = "sum",
        unit_label: str = "",
        display_config: DisplayConfig | None = None,
        date_column: str | None = None,
        source_type: str = "",
    ) -> None:
        """Initialize Excel source.

        Args:
            source_id: Unique identifier for this source.
            name: Display name for the source.
            file_path: Path to the Excel file.
            tabs: Dict mapping tab names to column ranges (standard),
                  or list of tab names (OKR).
            function: Aggregation function (currently only "sum").
            unit_label: Unit label for display.
            display_config: Optional display configuration for stats output.
            date_column: Optional date column for monthly comparison (e.g., "D3:D").
            source_type: Source type: "" for standard, "OKR" for OKR tracking.
        """
        self._source_id = source_id
        self._name = name
        self._file_path = file_path
        self._tabs = tabs
        self._function = function
        self._unit_label = unit_label
        self._display_config = display_config or DisplayConfig()
        self._date_column = date_column
        self._source_type = source_type
        self._reader: ExcelReader | None = None

    @property
    def is_okr(self) -> bool:
        """Return True if this is an OKR source."""
        return self._source_type.upper() == "OKR"

    @property
    def okr_tabs(self) -> list[str]:
        """Return list of OKR tab names."""
        if isinstance(self._tabs, list):
            return self._tabs
        return []

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

    @property
    def has_monthly_comparison(self) -> bool:
        """Return True if monthly comparison is available (date_column is set)."""
        return self._date_column is not None and not self.is_okr

    def _ensure_reader(self) -> ExcelReader:
        """Ensure reader is initialized and return it."""
        if self._reader is None:
            self._reader = ExcelReader(Path(self._file_path))
        return self._reader

    def get_selectable_items(self) -> list[SelectableItem]:
        """Return selectable items for this Excel source."""
        items: list[SelectableItem] = []

        if self.is_okr:
            # OKR source: one item per tab
            for tab_name in self.okr_tabs:
                label = f"{self._name} - {tab_name}"
                items.append(SelectableItem(None, label, "okr"))
            return items

        # Standard stats item
        label = self._name
        if self._unit_label:
            label = f"{self._name} ({self._unit_label})"
        items.append(SelectableItem(None, label, "stats"))

        # Monthly comparison item (if date_column is configured)
        if self.has_monthly_comparison:
            monthly_label = f"{self._name} - Monthly Comparison"
            if self._unit_label:
                monthly_label = f"{self._name} - Monthly ({self._unit_label})"
            items.append(SelectableItem(None, monthly_label, "monthly_comparison"))

        return items

    def get_item_name(self, item_id: int | None, item_type: str) -> str | None:
        """Get the name of an item.

        Args:
            item_id: Ignored for Excel sources.
            item_type: "stats", "monthly_comparison", or "okr".

        Returns:
            The item name.
        """
        if item_type == "okr":
            return self._name
        if item_type == "stats":
            label = self._name
            if self._unit_label:
                label = f"{self._name} ({self._unit_label})"
            return label
        elif item_type == "monthly_comparison":
            label = f"{self._name} - Monthly Comparison"
            if self._unit_label:
                label = f"{self._name} - Monthly ({self._unit_label})"
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

        Raises:
            ValueError: If called on an OKR source.
        """
        if self.is_okr:
            raise ValueError("OKR sources do not support data providers")
        reader = self._ensure_reader()
        return ExcelDataProvider(reader, self._tabs)  # type: ignore[arg-type]

    def get_stats(
        self, item_id: int | None = None, item_type: str | None = None
    ) -> TimeStats:
        """Calculate statistics for this Excel source.

        Args:
            item_id: Ignored (Excel has single stats per source).
            item_type: Ignored (always calculates same stats).

        Returns:
            TimeStats with all calculated periods.

        Raises:
            ValueError: If called on an OKR source.
        """
        if self.is_okr:
            raise ValueError("OKR sources do not support time stats")
        provider = self.get_data_provider(item_id, item_type)
        calculator = StatsCalculator()
        return calculator.calculate(provider.get_sum, self._display_config.show_years)

    def get_monthly_stats(self) -> MonthlyStats | None:
        """Get monthly comparison statistics.

        Returns:
            MonthlyStats if date_column is configured, None otherwise.
        """
        if not self.has_monthly_comparison:
            return None

        reader = self._ensure_reader()
        provider = MonthlyDataProvider(
            reader=reader,
            tabs=self._tabs,  # type: ignore[arg-type]
            date_column=self._date_column,  # type: ignore[arg-type]
            unit_label=self._unit_label,
        )
        return provider.get_monthly_stats()

    def get_okr_stats(self, tab_name: str) -> OkrStats | None:
        """Get OKR Key Result statistics for a specific tab.

        Args:
            tab_name: Name of the OKR worksheet/tab.

        Returns:
            OkrStats with parsed Key Results, or None if unavailable.
        """
        if not self.is_okr:
            return None

        reader = self._ensure_reader()
        return reader.get_okr_data(tab_name)

    def close(self) -> None:
        """Close resources."""
        if self._reader is not None:
            self._reader.close()
            self._reader = None
