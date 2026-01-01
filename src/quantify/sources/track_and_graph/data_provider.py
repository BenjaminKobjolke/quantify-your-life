"""Data providers for Track & Graph source."""

from datetime import UTC, date, datetime

from quantify.db.repositories.datapoints import DataPointsRepository


def _date_to_epoch_milli(d: date) -> int:
    """Convert a date to epoch milliseconds at start of day UTC."""
    dt = datetime(d.year, d.month, d.day, tzinfo=UTC)
    return int(dt.timestamp() * 1000)


def _date_to_end_of_day_epoch_milli(d: date) -> int:
    """Convert a date to epoch milliseconds at end of day UTC."""
    dt = datetime(d.year, d.month, d.day, 23, 59, 59, 999999, tzinfo=UTC)
    return int(dt.timestamp() * 1000)


class FeatureDataProvider:
    """Data provider for a single feature."""

    def __init__(self, repo: DataPointsRepository, feature_id: int) -> None:
        """Initialize provider.

        Args:
            repo: DataPoints repository instance.
            feature_id: The feature ID to query.
        """
        self._repo = repo
        self._feature_id = feature_id

    def get_sum(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> float:
        """Get sum of values for this feature in date range.

        Args:
            start_date: First day to include (None for no lower bound).
            end_date: Last day to include (None for today).

        Returns:
            Sum of values in seconds.
        """
        start_epoch = _date_to_epoch_milli(start_date) if start_date else None
        end_epoch = _date_to_end_of_day_epoch_milli(end_date) if end_date else None

        return self._repo.get_sum_by_feature(
            self._feature_id,
            start_epoch,
            end_epoch,
        )


class GroupDataProvider:
    """Data provider for a group (aggregates all features in the group)."""

    def __init__(self, repo: DataPointsRepository, feature_ids: list[int]) -> None:
        """Initialize provider.

        Args:
            repo: DataPoints repository instance.
            feature_ids: List of feature IDs in the group.
        """
        self._repo = repo
        self._feature_ids = feature_ids

    def get_sum(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> float:
        """Get sum of values for all features in this group.

        Args:
            start_date: First day to include (None for no lower bound).
            end_date: Last day to include (None for today).

        Returns:
            Sum of values in seconds.
        """
        if not self._feature_ids:
            return 0.0

        start_epoch = _date_to_epoch_milli(start_date) if start_date else None
        end_epoch = _date_to_end_of_day_epoch_milli(end_date) if end_date else None

        return self._repo.get_sum_by_features(
            self._feature_ids,
            start_epoch,
            end_epoch,
        )
