"""Data provider for Hometrainer source."""

from datetime import date

from quantify.sources.hometrainer.log_reader import HometrainerLogReader

# Conversion factor: 1 mile = 1.60934 kilometers
MILES_TO_KM = 1.60934


class HometrainerDataProvider:
    """Data provider for Hometrainer that handles unit conversion."""

    def __init__(self, log_reader: HometrainerLogReader, unit: str = "km") -> None:
        """Initialize provider.

        Args:
            log_reader: Log reader instance.
            unit: Display unit - "km" or "mi". Default is "km".
        """
        self._reader = log_reader
        self._unit = unit

    def get_sum(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> float:
        """Get sum of distance in date range.

        Values are converted to the configured unit.

        Args:
            start_date: First day to include (None for no lower bound).
            end_date: Last day to include (None for today).

        Returns:
            Sum of distance in the configured unit.
        """
        miles = self._reader.get_sum(start_date, end_date)

        if self._unit == "km":
            return miles * MILES_TO_KM
        return miles
