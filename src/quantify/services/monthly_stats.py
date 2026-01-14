"""Monthly comparison statistics."""

from dataclasses import dataclass


@dataclass
class MonthlyStats:
    """Statistics for monthly year-over-year comparison.

    Attributes:
        data: Monthly sums by year. Format: {year: {month: sum, ...}, ...}
              Example: {2024: {1: 1000.0, 2: 1500.0, ...}, 2023: {...}}
        years: Sorted list of years (newest first).
        unit_label: Unit label for display (e.g., "EUR", "kg").
    """

    data: dict[int, dict[int, float]]
    years: tuple[int, ...]
    unit_label: str

    @property
    def month_labels(self) -> tuple[str, ...]:
        """Get month labels for chart display."""
        return (
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        )

    def get_month_values(self, year: int) -> list[float]:
        """Get values for all 12 months for a specific year.

        Args:
            year: The year to get values for.

        Returns:
            List of 12 values (one per month), with 0.0 for missing months.
        """
        year_data = self.data.get(year, {})
        return [year_data.get(month, 0.0) for month in range(1, 13)]
