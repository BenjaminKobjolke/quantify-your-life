"""Application settings loaded from config file."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantify.config.constants import Constants
from quantify.utils.json_utils import JsonUtils


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""


# Source-specific configs


@dataclass(frozen=True)
class TrackAndGraphConfig:
    """Configuration for Track & Graph data source."""

    db_path: str


@dataclass(frozen=True)
class HometrainerConfig:
    """Configuration for Hometrainer data source."""

    logs_path: str
    unit: str = "km"  # "km" or "mi"


@dataclass(frozen=True)
class GitStatsConfig:
    """Configuration for Git statistics data source."""

    author: str
    root_paths: tuple[str, ...]
    exclude_dirs: tuple[str, ...] = (
        # Python
        "venv",
        ".venv",
        "env",
        ".env",
        "__pycache__",
        ".pytest_cache",
        ".tox",
        ".mypy_cache",
        "htmlcov",
        ".eggs",
        # Node.js / TypeScript
        "node_modules",
        ".npm",
        ".yarn",
        ".pnpm-store",
        ".next",
        ".nuxt",
        ".cache",
        "coverage",
        ".turbo",
        # PHP
        "vendor",
        # Java / Kotlin / Android
        "target",
        ".gradle",
        ".m2",
        # C# / .NET
        "bin",
        "obj",
        "packages",
        ".nuget",
        # Unity
        "Library",
        "Temp",
        "Logs",
        # Flutter / Dart
        ".dart_tool",
        ".pub-cache",
        ".pub",
        # General build output
        "build",
        "dist",
        "out",
        "output",
        "_build",
        # IDE / Editor
        ".idea",
        ".vscode",
        ".vs",
        # Xcode
        ".xcodeproj",
        ".xcworkspace",
    )
    exclude_extensions: tuple[str, ...] = (
        # Lock files (machine-generated)
        ".lock",
        # Config/data files
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".properties",
        ".plist",
        # Documentation
        ".md",
        ".txt",
        ".rst",
        ".adoc",
        ".org",
        # Web content (non-logic)
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".sass",
        ".less",
        # Media / Assets
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".webp",
        ".mp4",
        ".mp3",
        ".wav",
        ".pdf",
        ".ttf",
        ".woff",
        ".woff2",
        ".eot",
        # Data files
        ".csv",
        ".sql",
        ".db",
        ".sqlite",
        # Generated Dart/Flutter files
        ".g.dart",
        ".freezed.dart",
        ".gr.dart",
        ".mocks.dart",
        ".g.kt",
        # Generated TypeScript/JS
        ".d.ts",
        ".min.js",
        ".min.css",
        ".map",
        # Other generated
        ".generated.cs",
        ".designer.cs",
        # Unity
        ".meta",
        # Xcode / iOS
        ".pbxproj",
        ".xcscheme",
        ".xcworkspacedata",
        ".xcsettings",
        ".xcconfig",
        ".storyboard",
        # Android / Gradle
        ".gradle",
    )
    exclude_filenames: tuple[str, ...] = (
        # Lock files by name
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "Pipfile.lock",
        "poetry.lock",
        "composer.lock",
        "Gemfile.lock",
        "Cargo.lock",
        "go.sum",
        "pubspec.lock",
        # Other generated
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
    )


@dataclass(frozen=True)
class ProjectTypeConfig:
    """Configuration for a specific project type.

    Defines detection criteria and filtering rules for different project types.
    """

    name: str
    detection_files: tuple[str, ...] = ()  # Files that indicate this project type
    detection_dirs: tuple[str, ...] = ()  # Directories that indicate this project type
    include_patterns: tuple[str, ...] = ()  # If set, ONLY count files matching these
    exclude_dirs: tuple[str, ...] = ()  # Additional dirs to exclude for this type
    exclude_extensions: tuple[str, ...] = ()  # Additional extensions to exclude


# Default project type configurations
DEFAULT_PROJECT_TYPES: dict[str, ProjectTypeConfig] = {
    "unity": ProjectTypeConfig(
        name="unity",
        detection_files=("*.sln",),
        detection_dirs=("Assets", "ProjectSettings"),
        include_patterns=("Assets/Scripts/**/*.cs", "Assets/**/*.cs"),
        exclude_dirs=("Library", "Temp", "Logs", "Builds", "obj"),
    ),
    "flutter": ProjectTypeConfig(
        name="flutter",
        detection_files=("pubspec.yaml",),
        detection_dirs=(),
        include_patterns=("lib/**/*.dart",),
        exclude_dirs=(
            ".dart_tool",
            ".pub-cache",
            ".pub",
            "build",
            "android",
            "ios",
            "linux",
            "macos",
            "windows",
            "web",
        ),
    ),
    "python": ProjectTypeConfig(
        name="python",
        detection_files=("pyproject.toml", "setup.py", "requirements.txt"),
        detection_dirs=(),
        include_patterns=(),  # Use global exclusions
        exclude_dirs=("venv", ".venv", "env", ".env", "__pycache__", ".pytest_cache"),
    ),
    "node": ProjectTypeConfig(
        name="node",
        detection_files=("package.json",),
        detection_dirs=(),
        include_patterns=(),  # Use global exclusions
        exclude_dirs=("node_modules", ".npm", ".yarn", "dist", "build"),
    ),
    "arduino": ProjectTypeConfig(
        name="arduino",
        detection_files=("platformio.ini", "*.ino"),
        detection_dirs=(),
        include_patterns=("src/**/*", "*.ino", "*.cpp", "*.c", "*.h"),
        exclude_dirs=(".pio", ".pioenvs", ".piolibdeps", "lib"),
    ),
    "go": ProjectTypeConfig(
        name="go",
        detection_files=("go.mod",),
        detection_dirs=(),
        include_patterns=(),  # Use global exclusions
        exclude_dirs=("vendor",),
    ),
    "rust": ProjectTypeConfig(
        name="rust",
        detection_files=("Cargo.toml",),
        detection_dirs=(),
        include_patterns=(),  # Use global exclusions
        exclude_dirs=("target",),
    ),
    "generic": ProjectTypeConfig(
        name="generic",
        detection_files=(),
        detection_dirs=(),
        include_patterns=(),  # Use global exclusions only
        exclude_dirs=(),
    ),
}


@dataclass(frozen=True)
class SourcesConfig:
    """Configuration for all data sources."""

    track_and_graph: TrackAndGraphConfig | None = None
    hometrainer: HometrainerConfig | None = None
    git_stats: GitStatsConfig | None = None


# Export config


@dataclass(frozen=True)
class FtpSyncSettings:
    """FTP synchronization settings."""

    enabled: bool
    host: str
    username: str
    password: str
    remote_path: str
    port: int = 21
    passive_mode: bool = True
    timeout: int = 30


@dataclass(frozen=True)
class ExportEntry:
    """A single entry in the export configuration."""

    source: str  # "track_and_graph" or "hometrainer"
    entry_type: str  # "group", "feature", "stats", "top_features"
    entry_id: int | None  # None for hometrainer
    period: str | None = None  # For top_features: period key (e.g., "last_7_days")


@dataclass(frozen=True)
class ExportSettings:
    """Export configuration settings."""

    path: str
    entries: tuple[ExportEntry, ...]
    ftp_sync: FtpSyncSettings | None = None


# Legacy export settings for backwards compatibility


@dataclass(frozen=True)
class LegacyExportSettings:
    """Legacy export configuration (groups/features without source)."""

    path: str
    groups: tuple[int, ...]
    features: tuple[int, ...]


@dataclass(frozen=True)
class Settings:
    """Application settings."""

    sources: SourcesConfig
    export: ExportSettings | None = None

    @classmethod
    def load(cls, base_dir: Path | None = None) -> "Settings":
        """Load settings from config.json.

        Supports both old format (db_path at root) and new format (sources object).

        Args:
            base_dir: Base directory containing config.json. Defaults to cwd.

        Returns:
            Settings instance with loaded configuration.

        Raises:
            ConfigError: If config file not found or invalid.
        """
        if base_dir is None:
            base_dir = Path.cwd()

        config_path = base_dir / Constants.CONFIG_FILE_NAME

        if not config_path.exists():
            raise ConfigError(Constants.ERROR_CONFIG_NOT_FOUND.format(path=config_path))

        with open(config_path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ConfigError(
                    f"Invalid JSON in {config_path}: {e.msg} at line {e.lineno}, column {e.colno}"
                ) from e

        # Check for new format vs old format
        if "sources" in data:
            return cls._load_new_format(data)
        elif "db_path" in data:
            return cls._load_legacy_format(data)
        else:
            raise ConfigError("Config must have either 'sources' or 'db_path'")

    @classmethod
    def load_project(
        cls,
        project_path: Path,
        global_config_path: Path | None = None,
    ) -> "Settings":
        """Load settings for a specific project with optional global config merge.

        If global_config_path exists, its settings are used as defaults.
        Project-specific settings override global settings.

        Args:
            project_path: Path to project directory containing config.json.
            global_config_path: Optional path to global config.json.

        Returns:
            Settings instance with merged configuration.

        Raises:
            ConfigError: If neither project nor global config exists,
                        or if the merged config is invalid.
        """
        project_config_path = project_path / Constants.CONFIG_FILE_NAME
        has_project_config = project_config_path.exists()
        has_global_config = global_config_path and global_config_path.exists()

        if not has_project_config and not has_global_config:
            raise ConfigError(
                f"No configuration found. Expected config at: {project_config_path}"
            )

        # If only global config exists, use it directly
        if not has_project_config and has_global_config:
            assert global_config_path is not None  # for type checker
            return cls.load(global_config_path.parent)

        # If only project config exists, use it directly
        if has_project_config and not has_global_config:
            return cls.load(project_path)

        # Both exist - merge them
        try:
            merged_data = JsonUtils.load_and_merge(global_config_path, project_config_path)
        except json.JSONDecodeError as e:
            raise ConfigError(
                f"Invalid JSON: {e.msg} at line {e.lineno}, column {e.colno}"
            ) from e

        # Check for new format vs old format
        if "sources" in merged_data:
            return cls._load_new_format(merged_data)
        elif "db_path" in merged_data:
            return cls._load_legacy_format(merged_data)
        else:
            raise ConfigError("Config must have either 'sources' or 'db_path'")

    @classmethod
    def _load_new_format(cls, data: dict[str, Any]) -> "Settings":
        """Load configuration from new format with sources object."""
        sources_data = data.get("sources", {})

        # Track & Graph config
        track_and_graph_config = None
        tg_data = sources_data.get("track_and_graph")
        if tg_data and tg_data.get("db_path"):
            track_and_graph_config = TrackAndGraphConfig(db_path=tg_data["db_path"])

        # Hometrainer config
        hometrainer_config = None
        ht_data = sources_data.get("hometrainer")
        if ht_data and ht_data.get("logs_path"):
            hometrainer_config = HometrainerConfig(
                logs_path=ht_data["logs_path"],
                unit=ht_data.get("unit", "km"),
            )

        # Git Stats config
        git_stats_config = None
        gs_data = sources_data.get("git_stats")
        if gs_data and gs_data.get("author") and gs_data.get("root_paths"):
            git_stats_config = GitStatsConfig(
                author=gs_data["author"],
                root_paths=tuple(gs_data["root_paths"]),
                exclude_dirs=tuple(gs_data.get("exclude_dirs", GitStatsConfig.exclude_dirs)),
                exclude_extensions=tuple(
                    gs_data.get("exclude_extensions", GitStatsConfig.exclude_extensions)
                ),
                exclude_filenames=tuple(
                    gs_data.get("exclude_filenames", GitStatsConfig.exclude_filenames)
                ),
            )

        sources_config = SourcesConfig(
            track_and_graph=track_and_graph_config,
            hometrainer=hometrainer_config,
            git_stats=git_stats_config,
        )

        # Export settings
        export_settings = None
        export_data = data.get("export")
        if export_data:
            entries: list[ExportEntry] = []
            for entry_data in export_data.get("entries", []):
                entries.append(
                    ExportEntry(
                        source=entry_data["source"],
                        entry_type=entry_data["type"],
                        entry_id=entry_data.get("id"),
                        period=entry_data.get("period"),
                    )
                )

            # FTP sync settings
            ftp_sync_settings = None
            ftp_data = export_data.get("ftp_sync")
            if ftp_data:
                ftp_sync_settings = FtpSyncSettings(
                    enabled=ftp_data.get("enabled", False),
                    host=ftp_data.get("host", ""),
                    username=ftp_data.get("username", ""),
                    password=ftp_data.get("password", ""),
                    remote_path=ftp_data.get("remote_path", ""),
                    port=ftp_data.get("port", 21),
                    passive_mode=ftp_data.get("passive_mode", True),
                    timeout=ftp_data.get("timeout", 30),
                )

            export_settings = ExportSettings(
                path=export_data.get("path", ""),
                entries=tuple(entries),
                ftp_sync=ftp_sync_settings,
            )

        return cls(sources=sources_config, export=export_settings)

    @classmethod
    def _load_legacy_format(cls, data: dict[str, Any]) -> "Settings":
        """Load configuration from legacy format (db_path at root).

        Converts to new format internally while preserving export entries.
        """
        db_path = data.get("db_path")
        if not db_path:
            raise ConfigError("db_path is required in config.json")

        # Create sources config from legacy db_path
        sources_config = SourcesConfig(
            track_and_graph=TrackAndGraphConfig(db_path=db_path),
            hometrainer=None,
            git_stats=None,
        )

        # Convert legacy export settings to new format
        export_settings = None
        export_data = data.get("export")
        if export_data:
            entries: list[ExportEntry] = []

            # Convert legacy groups to entries
            for group_id in export_data.get("groups", []):
                entries.append(
                    ExportEntry(
                        source="track_and_graph",
                        entry_type="group",
                        entry_id=group_id,
                    )
                )

            # Convert legacy features to entries
            for feature_id in export_data.get("features", []):
                entries.append(
                    ExportEntry(
                        source="track_and_graph",
                        entry_type="feature",
                        entry_id=feature_id,
                    )
                )

            export_settings = ExportSettings(
                path=export_data.get("path", ""),
                entries=tuple(entries),
            )

        return cls(sources=sources_config, export=export_settings)

    @property
    def db_path(self) -> str | None:
        """Get Track & Graph database path (for backwards compatibility)."""
        if self.sources.track_and_graph:
            return self.sources.track_and_graph.db_path
        return None
