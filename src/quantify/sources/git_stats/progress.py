"""Progress display mixin for git stats operations."""

from collections.abc import Iterator
from contextlib import contextmanager

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
)


class ProgressMixin:
    """Mixin providing progress display functionality.

    Displays single line: [spinner] status [bar] X/Y

    Attributes:
        _console: Rich console instance.
        _progress: Current Progress instance or None.
        _task_id: Current task ID or None.
    """

    _console: Console
    _progress: Progress | None
    _task_id: TaskID | None

    @contextmanager
    def _progress_context(
        self,
        description: str,
        total: int | None = None,
    ) -> Iterator[Progress]:
        """Create a unified progress display context.

        Args:
            description: Initial status text.
            total: Total count for progress bar, or None for indeterminate.

        Yields:
            Progress instance for updates.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.fields[status]}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=self._console,
            transient=False,
        ) as progress:
            self._progress = progress
            self._task_id = progress.add_task("", total=total, status=description)
            try:
                yield progress
            finally:
                self._progress = None
                self._task_id = None

    def _on_progress(self, repo_name: str, current: int, total: int) -> None:
        """Callback for progress updates during data provider operations.

        Args:
            repo_name: Name of the repository currently being processed.
            current: Current repository index (1-based).
            total: Total number of repositories.
        """
        if self._progress is None or self._task_id is None:
            return

        self._progress.update(
            self._task_id,
            total=total,
            completed=current,
            status=f"Scanning: {repo_name}",
        )
