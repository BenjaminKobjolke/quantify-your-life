"""Repository for features_table operations."""

from dataclasses import dataclass

from quantify.db.connection import Database


@dataclass
class Feature:
    """Feature entity."""

    id: int
    name: str
    group_id: int
    display_index: int
    description: str


class FeaturesRepository:
    """Repository for accessing features data."""

    def __init__(self, db: Database) -> None:
        """Initialize repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    def get_all(self) -> list[Feature]:
        """Get all features ordered by display_index.

        Returns:
            List of all features.
        """
        query = """
            SELECT id, name, group_id, display_index, feature_description
            FROM features_table
            ORDER BY display_index
        """
        rows = self._db.execute(query)
        return [
            Feature(
                id=row["id"],
                name=row["name"],
                group_id=row["group_id"],
                display_index=row["display_index"],
                description=row["feature_description"],
            )
            for row in rows
        ]

    def get_by_group_id(self, group_id: int) -> list[Feature]:
        """Get all features belonging to a group.

        Args:
            group_id: The group ID to filter by.

        Returns:
            List of features in the group.
        """
        query = """
            SELECT id, name, group_id, display_index, feature_description
            FROM features_table
            WHERE group_id = ?
            ORDER BY display_index
        """
        rows = self._db.execute(query, (group_id,))
        return [
            Feature(
                id=row["id"],
                name=row["name"],
                group_id=row["group_id"],
                display_index=row["display_index"],
                description=row["feature_description"],
            )
            for row in rows
        ]

    def get_by_id(self, feature_id: int) -> Feature | None:
        """Get a feature by ID.

        Args:
            feature_id: The feature ID to find.

        Returns:
            Feature if found, None otherwise.
        """
        query = """
            SELECT id, name, group_id, display_index, feature_description
            FROM features_table
            WHERE id = ?
        """
        rows = self._db.execute(query, (feature_id,))
        if not rows:
            return None
        row = rows[0]
        return Feature(
            id=row["id"],
            name=row["name"],
            group_id=row["group_id"],
            display_index=row["display_index"],
            description=row["feature_description"],
        )
