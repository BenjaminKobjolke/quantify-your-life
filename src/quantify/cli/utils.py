"""Utility functions for CLI operations."""

import contextlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console


def export_exclusion_log(
    repo_path: Path, analysis: dict[str, object], console: Console | None = None
) -> Path:
    """Export exclusion analysis to a log file.

    Args:
        repo_path: Path to the repository.
        analysis: Exclusion analysis dict.
        console: Optional console for status messages.

    Returns:
        Path to the exported log file.
    """
    # Create logs directory in user's home
    log_dir = Path.home() / ".quantify-your-life" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in repo_path.name)
    log_path = log_dir / f"exclusions_{safe_name}_{timestamp}.txt"

    # Write log content
    lines: list[str] = []
    lines.append(f"Exclusion Analysis Report for: {repo_path.name}")
    lines.append(f"Full path: {repo_path}")
    lines.append(f"Generated at: {datetime.now().isoformat()}")
    lines.append("=" * 80)
    lines.append("")

    # Project type
    project_type = analysis.get("project_type")
    if project_type:
        lines.append(f"Project Type: {project_type}")
        lines.append("")

    # Total tracked
    lines.append(f"Total tracked files: {analysis['total_tracked']}")
    lines.append("")

    # Exclusion categories
    categories = [
        ("Excluded by directory", "excluded_by_dir"),
        ("Excluded by extension", "excluded_by_extension"),
        ("Excluded by filename", "excluded_by_filename"),
        ("Excluded by include pattern", "excluded_by_include_pattern"),
        ("Included files", "included_files"),
    ]

    for label, key in categories:
        data = analysis.get(key)
        if data and isinstance(data, dict):
            count = data.get("count", 0)
            examples = data.get("examples", [])
            lines.append(f"{label}: {count}")
            if examples:
                lines.append("  Examples:")
                for example in examples:
                    lines.append(f"    - {example}")
            lines.append("")

    # Write to file
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return log_path


def open_file(file_path: Path, console: Console | None = None) -> None:
    """Open a file with the system's default application.

    Args:
        file_path: Path to the file to open.
        console: Optional console for status messages.
    """
    path_str = str(file_path)
    if console:
        console.print(f"[dim]Opening: {path_str}[/dim]")

    try:
        if sys.platform == "win32":
            # Use subprocess.run with start command as it's more reliable
            subprocess.run(
                ["cmd", "/c", "start", "", path_str],
                check=False,
                shell=False,
            )
        elif sys.platform == "darwin":
            subprocess.run(["open", path_str], check=False)
        else:
            subprocess.run(["xdg-open", path_str], check=False)
    except Exception as e:
        if console:
            console.print(f"[red]Failed to open file: {e}[/red]")
        # Fallback: try notepad on Windows
        if sys.platform == "win32":
            with contextlib.suppress(Exception):
                subprocess.run(["notepad.exe", path_str], check=False)
