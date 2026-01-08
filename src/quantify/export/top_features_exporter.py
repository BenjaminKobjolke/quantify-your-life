"""Top features export functionality."""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from jinja2 import Environment

from quantify.cli.handlers.period_selector import get_period_date_range, get_period_label
from quantify.sources.track_and_graph import TrackAndGraphSource


def format_duration(seconds: float) -> str:
    """Format seconds as human-readable duration.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string like "5h 23m" or "45m".
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def export_top_features(
    env: Environment,
    output_dir: Path,
    source: TrackAndGraphSource,
    group_id: int,
    group_name: str,
    period_key: str,
    php_mode: bool = False,
    php_wrapper_func: Callable[[str], str] | None = None,
) -> Path:
    """Export top features chart for a group.

    Args:
        env: Jinja2 environment.
        output_dir: Output directory path.
        source: Track & Graph data source.
        group_id: ID of the group.
        group_name: Name of the group.
        period_key: Period key for filtering.
        php_mode: If True, output PHP file with authentication.
        php_wrapper_func: Function to wrap HTML with PHP auth code.

    Returns:
        Path to generated file.
    """
    template = env.get_template("top_features.html")

    # Get date range and label for period
    start_date, end_date = get_period_date_range(period_key)
    period_label = get_period_label(period_key)

    # Get top features
    top_features = source.get_top_features_in_group(group_id, start_date, end_date)

    # Build chart data
    chart_labels = [name for name, _ in top_features]
    chart_values = [value for _, value in top_features]

    # Build table items with formatted values
    top_items = [
        {"name": name, "formatted_value": format_duration(value)}
        for name, value in top_features
    ]

    title = f"Top Features - {group_name}"

    html_content = template.render(
        title=title,
        period_label=period_label,
        chart_labels=chart_labels,
        chart_values=chart_values,
        top_items=top_items,
        unit="time",
        unit_label="h",
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    # Generate filename with appropriate extension
    extension = ".php" if php_mode else ".html"
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in group_name)
    safe_period = "".join(c if c.isalnum() or c in "-_" else "_" for c in period_key)
    filename = f"track_and_graph_top_features_{group_id}_{safe_name}_{safe_period}{extension}"
    file_path = output_dir / filename

    # Wrap with PHP authentication if enabled
    content = html_content
    if php_mode and php_wrapper_func:
        content = php_wrapper_func(html_content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path
