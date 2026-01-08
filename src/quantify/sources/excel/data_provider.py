"""Data provider for Excel source."""

from datetime import date

from quantify.sources.excel.reader import ExcelReader


class ExcelDataProvider:
    """Data provider that aggregates Excel data by year.

    Maps date ranges to yearly totals:
    - Single year: Return that year's tab sum
    - Multiple years: Sum the relevant years
    - Partial years: Return full year data (approximation)
    """

    def __init__(
        self,
        reader: ExcelReader,
        tabs: dict[str, str],  # {tab_name: column_range}
    ) -> None:
        """Initialize provider.

        Args:
            reader: Excel file reader.
            tabs: Dict mapping tab names (years) to column ranges.
        """
        self._reader = reader
        self._tabs = tabs
        # Pre-compute year tab mapping for fast lookup
        self._year_to_tab = self._build_year_mapping()
        # Cache yearly sums
        self._yearly_cache: dict[str, float] = {}

    def _build_year_mapping(self) -> dict[int, str]:
        """Build mapping from year integers to tab names.

        Tab names like "2020", "2021" are mapped to int years.
        Non-numeric tabs are skipped.

        Returns:
            Dict mapping year (int) to tab name (str).
        """
        mapping: dict[int, str] = {}
        for tab in self._tabs:
            try:
                year = int(tab)
                mapping[year] = tab
            except ValueError:
                # Tab name is not a year, skip it
                continue
        return mapping

    def _get_year_sum(self, year: int) -> float:
        """Get cached sum for a year.

        Args:
            year: The year to get sum for.

        Returns:
            Sum for that year, or 0.0 if year not available.
        """
        tab_name = self._year_to_tab.get(year)
        if tab_name is None:
            return 0.0

        if tab_name not in self._yearly_cache:
            column_range_str = self._tabs[tab_name]
            column_range = ExcelReader.parse_column_range(column_range_str)
            self._yearly_cache[tab_name] = self._reader.get_tab_sum(tab_name, column_range)

        return self._yearly_cache[tab_name]

    def get_sum(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> float:
        """Get sum for date range.

        Since we only have yearly totals:
        - If date range is None/None: Return total of all years
        - If date range spans multiple years: Sum those years
        - Partial years: Return full year (acceptable approximation)

        Args:
            start_date: First day to include (None for no lower bound).
            end_date: Last day to include (None for today).

        Returns:
            Sum of values for the date range.
        """
        if end_date is None:
            end_date = date.today()

        # If no start date, sum ALL available years
        if start_date is None:
            return sum(self._get_year_sum(year) for year in self._year_to_tab)

        # Get years spanned by the date range
        start_year = start_date.year
        end_year = end_date.year

        # Sum all years in range
        total = 0.0
        for year in range(start_year, end_year + 1):
            total += self._get_year_sum(year)

        return total
