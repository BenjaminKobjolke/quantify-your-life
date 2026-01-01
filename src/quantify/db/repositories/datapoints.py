"""Repository for data_points_table operations."""

from dataclasses import dataclass

from quantify.db.connection import Database


@dataclass
class DataPoint:
    """Data point entity."""

    epoch_milli: int
    feature_id: int
    utc_offset_sec: int
    value: float
    label: str
    note: str


class DataPointsRepository:
    """Repository for accessing data points."""

    def __init__(self, db: Database) -> None:
        """Initialize repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    def get_sum_by_feature(
        self,
        feature_id: int,
        start_epoch_milli: int | None = None,
        end_epoch_milli: int | None = None,
    ) -> float:
        """Get sum of values for a feature within a time range.

        Args:
            feature_id: The feature ID to sum values for.
            start_epoch_milli: Start of time range (inclusive). None for no lower bound.
            end_epoch_milli: End of time range (inclusive). None for no upper bound.

        Returns:
            Sum of values in seconds.
        """
        conditions = ["feature_id = ?"]
        params: list[int] = [feature_id]

        if start_epoch_milli is not None:
            conditions.append("epoch_milli >= ?")
            params.append(start_epoch_milli)

        if end_epoch_milli is not None:
            conditions.append("epoch_milli <= ?")
            params.append(end_epoch_milli)

        query = f"""
            SELECT COALESCE(SUM(value), 0) as total
            FROM data_points_table
            WHERE {" AND ".join(conditions)}
        """
        rows = self._db.execute(query, tuple(params))
        return float(rows[0]["total"]) if rows else 0.0

    def get_sum_by_features(
        self,
        feature_ids: list[int],
        start_epoch_milli: int | None = None,
        end_epoch_milli: int | None = None,
    ) -> float:
        """Get sum of values for multiple features within a time range.

        Args:
            feature_ids: List of feature IDs to sum values for.
            start_epoch_milli: Start of time range (inclusive). None for no lower bound.
            end_epoch_milli: End of time range (inclusive). None for no upper bound.

        Returns:
            Sum of values in seconds.
        """
        if not feature_ids:
            return 0.0

        placeholders = ",".join("?" for _ in feature_ids)
        conditions = [f"feature_id IN ({placeholders})"]
        params: list[int] = list(feature_ids)

        if start_epoch_milli is not None:
            conditions.append("epoch_milli >= ?")
            params.append(start_epoch_milli)

        if end_epoch_milli is not None:
            conditions.append("epoch_milli <= ?")
            params.append(end_epoch_milli)

        query = f"""
            SELECT COALESCE(SUM(value), 0) as total
            FROM data_points_table
            WHERE {" AND ".join(conditions)}
        """
        rows = self._db.execute(query, tuple(params))
        return float(rows[0]["total"]) if rows else 0.0
