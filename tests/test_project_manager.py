"""Tests for ProjectManager."""

from pathlib import Path

from quantify.config.project_manager import ProjectInfo, ProjectManager


class TestProjectManager:
    """Tests for ProjectManager class."""

    def test_projects_dir_path(self, tmp_path: Path) -> None:
        """Test that projects directory path is correct."""
        pm = ProjectManager(tmp_path)
        assert pm.get_projects_dir() == tmp_path / "projects"

    def test_base_dir_path(self, tmp_path: Path) -> None:
        """Test that base directory path is correct."""
        pm = ProjectManager(tmp_path)
        assert pm.get_base_dir() == tmp_path

    def test_projects_exist_false_when_no_dir(self, tmp_path: Path) -> None:
        """Test projects_exist returns False when no projects dir."""
        pm = ProjectManager(tmp_path)
        assert pm.projects_exist() is False

    def test_projects_exist_false_when_empty_dir(self, tmp_path: Path) -> None:
        """Test projects_exist returns False when projects dir is empty."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        pm = ProjectManager(tmp_path)
        assert pm.projects_exist() is False

    def test_projects_exist_true_with_project(self, tmp_path: Path) -> None:
        """Test projects_exist returns True when project exists."""
        projects_dir = tmp_path / "projects"
        (projects_dir / "test-project").mkdir(parents=True)

        pm = ProjectManager(tmp_path)
        assert pm.projects_exist() is True

    def test_has_legacy_config_false_when_missing(self, tmp_path: Path) -> None:
        """Test has_legacy_config returns False when no config."""
        pm = ProjectManager(tmp_path)
        assert pm.has_legacy_config() is False

    def test_has_legacy_config_true_when_exists(self, tmp_path: Path) -> None:
        """Test has_legacy_config returns True when config exists."""
        (tmp_path / "config.json").write_text("{}")

        pm = ProjectManager(tmp_path)
        assert pm.has_legacy_config() is True

    def test_discover_projects_empty(self, tmp_path: Path) -> None:
        """Test discover_projects returns empty list when no projects."""
        pm = ProjectManager(tmp_path)
        assert pm.discover_projects() == []

    def test_discover_projects_finds_projects(self, tmp_path: Path) -> None:
        """Test discover_projects finds project directories."""
        projects_dir = tmp_path / "projects"
        (projects_dir / "project-a").mkdir(parents=True)
        (projects_dir / "project-b").mkdir(parents=True)

        pm = ProjectManager(tmp_path)
        projects = pm.discover_projects()

        assert len(projects) == 2
        assert projects[0].name == "project-a"
        assert projects[1].name == "project-b"

    def test_discover_projects_detects_config(self, tmp_path: Path) -> None:
        """Test discover_projects detects config.json presence."""
        projects_dir = tmp_path / "projects"
        project_with_config = projects_dir / "with-config"
        project_without_config = projects_dir / "without-config"

        project_with_config.mkdir(parents=True)
        project_without_config.mkdir(parents=True)
        (project_with_config / "config.json").write_text("{}")

        pm = ProjectManager(tmp_path)
        projects = pm.discover_projects()

        projects_dict = {p.name: p for p in projects}
        assert projects_dict["with-config"].has_config is True
        assert projects_dict["without-config"].has_config is False

    def test_discover_projects_ignores_hidden(self, tmp_path: Path) -> None:
        """Test discover_projects ignores hidden directories."""
        projects_dir = tmp_path / "projects"
        (projects_dir / "visible").mkdir(parents=True)
        (projects_dir / ".hidden").mkdir(parents=True)

        pm = ProjectManager(tmp_path)
        projects = pm.discover_projects()

        assert len(projects) == 1
        assert projects[0].name == "visible"

    def test_discover_projects_sorted(self, tmp_path: Path) -> None:
        """Test discover_projects returns sorted list."""
        projects_dir = tmp_path / "projects"
        (projects_dir / "zebra").mkdir(parents=True)
        (projects_dir / "alpha").mkdir(parents=True)
        (projects_dir / "beta").mkdir(parents=True)

        pm = ProjectManager(tmp_path)
        projects = pm.discover_projects()

        names = [p.name for p in projects]
        assert names == ["alpha", "beta", "zebra"]

    def test_get_project_path(self, tmp_path: Path) -> None:
        """Test get_project_path returns correct path."""
        pm = ProjectManager(tmp_path)
        path = pm.get_project_path("my-project")
        assert path == tmp_path / "projects" / "my-project"

    def test_get_global_config_path(self, tmp_path: Path) -> None:
        """Test get_global_config_path returns correct path."""
        pm = ProjectManager(tmp_path)
        path = pm.get_global_config_path()
        assert path == tmp_path / "projects" / "config.json"

    def test_project_exists_false(self, tmp_path: Path) -> None:
        """Test project_exists returns False when project doesn't exist."""
        pm = ProjectManager(tmp_path)
        assert pm.project_exists("nonexistent") is False

    def test_project_exists_true(self, tmp_path: Path) -> None:
        """Test project_exists returns True when project exists."""
        (tmp_path / "projects" / "existing").mkdir(parents=True)

        pm = ProjectManager(tmp_path)
        assert pm.project_exists("existing") is True

    def test_create_project(self, tmp_path: Path) -> None:
        """Test create_project creates directory."""
        pm = ProjectManager(tmp_path)
        path = pm.create_project("new-project")

        assert path.exists()
        assert path.is_dir()
        assert path == tmp_path / "projects" / "new-project"

    def test_create_project_creates_parents(self, tmp_path: Path) -> None:
        """Test create_project creates parent directories."""
        pm = ProjectManager(tmp_path)

        # projects/ doesn't exist yet
        assert not (tmp_path / "projects").exists()

        pm.create_project("new-project")

        assert (tmp_path / "projects").exists()
        assert (tmp_path / "projects" / "new-project").exists()

    def test_create_project_idempotent(self, tmp_path: Path) -> None:
        """Test create_project is idempotent."""
        pm = ProjectManager(tmp_path)

        path1 = pm.create_project("my-project")
        path2 = pm.create_project("my-project")

        assert path1 == path2
        assert path1.exists()


class TestProjectInfo:
    """Tests for ProjectInfo dataclass."""

    def test_frozen(self) -> None:
        """Test that ProjectInfo is immutable."""
        info = ProjectInfo(name="test", path=Path("/test"), has_config=True)

        # Should raise FrozenInstanceError
        try:
            info.name = "changed"  # type: ignore
            raise AssertionError("Should have raised an error")
        except AttributeError:
            pass
