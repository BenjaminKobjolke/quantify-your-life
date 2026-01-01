"""Registry for managing data sources."""

from quantify.sources.base import DataSource


class SourceRegistry:
    """Registry for managing available data sources.

    The registry holds references to all data sources and provides
    methods to query configured sources.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._sources: dict[str, DataSource] = {}

    def register(self, source: DataSource) -> None:
        """Register a data source.

        Args:
            source: The data source to register.
        """
        self._sources[source.info.id] = source

    def get_by_id(self, source_id: str) -> DataSource | None:
        """Get a source by its ID.

        Args:
            source_id: The source identifier (e.g., "track_and_graph").

        Returns:
            The source if found, None otherwise.
        """
        return self._sources.get(source_id)

    def get_all(self) -> list[DataSource]:
        """Get all registered sources.

        Returns:
            List of all registered sources.
        """
        return list(self._sources.values())

    def get_configured_sources(self) -> list[DataSource]:
        """Get only sources that are properly configured.

        Returns:
            List of sources where is_configured() returns True.
        """
        return [s for s in self._sources.values() if s.is_configured()]

    def close_all(self) -> None:
        """Close all registered sources."""
        for source in self._sources.values():
            source.close()
