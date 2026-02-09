"""OKR (Objectives & Key Results) statistics data model."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class OkrKeyResult:
    """A single Key Result with its progress data over time.

    Attributes:
        name: KR header text (e.g., "KR1 Klicks/w bei Google").
        target: Target value from the "Ziele" row.
        data_points: List of (date, percentage) tuples.
                     Percentage is 0-100 scale.
    """

    name: str
    target: float
    data_points: list[tuple[datetime, float]]


@dataclass
class OkrStats:
    """Statistics for one OKR tab containing multiple Key Results.

    Attributes:
        tab_name: Name of the Excel tab.
        key_results: List of Key Results with their progress data.
        target_date: Optional target date ("Zieldatum") for prognosis calculation.
    """

    tab_name: str
    key_results: list[OkrKeyResult]
    target_date: datetime | None = field(default=None)
