"""Track & Graph data source implementation."""

from pathlib import Path

from quantify.db.connection import Database
from quantify.db.repositories.datapoints import DataPointsRepository
from quantify.db.repositories.features import FeaturesRepository
from quantify.db.repositories.groups import GroupsRepository
from quantify.services.stats_calculator import StatsCalculator, TimeStats
from quantify.sources.base import DataProvider, DataSource, SelectableItem, SourceInfo
from quantify.sources.track_and_graph.data_provider import (
    FeatureDataProvider,
    GroupDataProvider,
)


class TrackAndGraphSource(DataSource):
    """Data source for Track & Graph SQLite database."""

    def __init__(self, db_path: str | None) -> None:
        """Initialize Track & Graph source.

        Args:
            db_path: Path to the Track & Graph SQLite database.
        """
        self._db_path = db_path
        self._db: Database | None = None
        self._groups_repo: GroupsRepository | None = None
        self._features_repo: FeaturesRepository | None = None
        self._datapoints_repo: DataPointsRepository | None = None

    @property
    def info(self) -> SourceInfo:
        """Return metadata about this source."""
        return SourceInfo(
            id="track_and_graph",
            display_name="Track & Graph",
            unit="time",
            unit_label="h",
        )

    def is_configured(self) -> bool:
        """Return True if database path is set and file exists."""
        if not self._db_path:
            return False
        return Path(self._db_path).exists()

    def _ensure_connected(self) -> None:
        """Ensure database connection and repositories are initialized."""
        if self._db is None:
            if not self._db_path:
                raise RuntimeError("Track & Graph source not configured")
            self._db = Database(self._db_path)
            self._groups_repo = GroupsRepository(self._db)
            self._features_repo = FeaturesRepository(self._db)
            self._datapoints_repo = DataPointsRepository(self._db)

    def get_selectable_items(self) -> list[SelectableItem]:
        """Return groups and features as selectable items."""
        self._ensure_connected()
        assert self._groups_repo is not None
        assert self._features_repo is not None

        items: list[SelectableItem] = []

        # Add groups
        for group in self._groups_repo.get_all():
            items.append(SelectableItem(group.id, group.name, "group"))

        # Add features
        for feature in self._features_repo.get_all():
            items.append(SelectableItem(feature.id, feature.name, "feature"))

        return items

    def get_groups(self) -> list[SelectableItem]:
        """Return only groups as selectable items."""
        self._ensure_connected()
        assert self._groups_repo is not None

        return [
            SelectableItem(group.id, group.name, "group")
            for group in self._groups_repo.get_all()
        ]

    def get_features(self) -> list[SelectableItem]:
        """Return only features as selectable items."""
        self._ensure_connected()
        assert self._features_repo is not None

        return [
            SelectableItem(feature.id, feature.name, "feature")
            for feature in self._features_repo.get_all()
        ]

    def get_item_name(self, item_id: int, item_type: str) -> str | None:
        """Get the name of an item by ID and type.

        Args:
            item_id: The item ID.
            item_type: "group" or "feature".

        Returns:
            The item name, or None if not found.
        """
        self._ensure_connected()

        if item_type == "group":
            assert self._groups_repo is not None
            group = self._groups_repo.get_by_id(item_id)
            return group.name if group else None
        elif item_type == "feature":
            assert self._features_repo is not None
            feature = self._features_repo.get_by_id(item_id)
            return feature.name if feature else None
        return None

    def get_data_provider(
        self, item_id: int | None = None, item_type: str | None = None
    ) -> DataProvider:
        """Get a data provider for the specified item.

        Args:
            item_id: ID of the group or feature.
            item_type: "group" or "feature".

        Returns:
            DataProvider for calculating sums.
        """
        self._ensure_connected()
        assert self._datapoints_repo is not None
        assert self._features_repo is not None

        if item_type == "group" and item_id is not None:
            # Get all feature IDs in this group
            features = self._features_repo.get_by_group_id(item_id)
            feature_ids = [f.id for f in features]
            return GroupDataProvider(self._datapoints_repo, feature_ids)
        elif item_type == "feature" and item_id is not None:
            return FeatureDataProvider(self._datapoints_repo, item_id)
        else:
            raise ValueError(f"Invalid item_type: {item_type} or item_id: {item_id}")

    def get_stats(
        self, item_id: int | None = None, item_type: str | None = None
    ) -> TimeStats:
        """Calculate statistics for the specified item.

        Args:
            item_id: ID of the group or feature.
            item_type: "group" or "feature".

        Returns:
            TimeStats with all calculated periods.
        """
        provider = self.get_data_provider(item_id, item_type)
        calculator = StatsCalculator()
        return calculator.calculate(provider.get_sum)

    def close(self) -> None:
        """Close the database connection."""
        if self._db is not None:
            self._db.close()
            self._db = None
            self._groups_repo = None
            self._features_repo = None
            self._datapoints_repo = None
