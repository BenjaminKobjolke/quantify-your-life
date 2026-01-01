"""Repository for groups_table operations."""

from dataclasses import dataclass

from quantify.db.connection import Database


@dataclass
class Group:
    """Group entity."""

    id: int
    name: str
    display_index: int
    parent_group_id: int | None
    color_index: int


class GroupsRepository:
    """Repository for accessing groups data."""

    def __init__(self, db: Database) -> None:
        """Initialize repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    def get_all(self) -> list[Group]:
        """Get all groups ordered by display_index.

        Returns:
            List of all groups.
        """
        query = """
            SELECT id, name, display_index, parent_group_id, color_index
            FROM groups_table
            ORDER BY display_index
        """
        rows = self._db.execute(query)
        return [
            Group(
                id=row["id"],
                name=row["name"],
                display_index=row["display_index"],
                parent_group_id=row["parent_group_id"],
                color_index=row["color_index"],
            )
            for row in rows
        ]

    def get_by_id(self, group_id: int) -> Group | None:
        """Get a group by ID.

        Args:
            group_id: The group ID to find.

        Returns:
            Group if found, None otherwise.
        """
        query = """
            SELECT id, name, display_index, parent_group_id, color_index
            FROM groups_table
            WHERE id = ?
        """
        rows = self._db.execute(query, (group_id,))
        if not rows:
            return None
        row = rows[0]
        return Group(
            id=row["id"],
            name=row["name"],
            display_index=row["display_index"],
            parent_group_id=row["parent_group_id"],
            color_index=row["color_index"],
        )
