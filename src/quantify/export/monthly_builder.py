"""Monthly comparison chart data builder for HTML export."""

from quantify.services.monthly_stats import MonthlyStats


# Color palette for years (newest to oldest)
YEAR_COLORS = [
    ("rgba(0, 212, 255, 0.7)", "rgba(0, 212, 255, 1)"),  # Cyan
    ("rgba(255, 159, 64, 0.7)", "rgba(255, 159, 64, 1)"),  # Orange
    ("rgba(153, 102, 255, 0.7)", "rgba(153, 102, 255, 1)"),  # Purple
    ("rgba(75, 192, 192, 0.7)", "rgba(75, 192, 192, 1)"),  # Teal
    ("rgba(255, 99, 132, 0.7)", "rgba(255, 99, 132, 1)"),  # Pink
    ("rgba(255, 205, 86, 0.7)", "rgba(255, 205, 86, 1)"),  # Yellow
    ("rgba(54, 162, 235, 0.7)", "rgba(54, 162, 235, 1)"),  # Blue
]


def build_monthly_chart_data(stats: MonthlyStats) -> dict:
    """Build Chart.js grouped bar chart data from MonthlyStats.

    Args:
        stats: Monthly comparison statistics.

    Returns:
        Dict with:
            - labels: List of month names ["Jan", "Feb", ...]
            - datasets: List of dataset dicts for Chart.js
            - unit_label: Unit label for display
    """
    labels = list(stats.month_labels)

    # Build datasets (one per year, oldest first for left-to-right chronological order)
    sorted_years = sorted(stats.years)  # Sort ascending (oldest first)
    datasets = []
    for idx, year in enumerate(sorted_years):
        color_idx = idx % len(YEAR_COLORS)
        bg_color, border_color = YEAR_COLORS[color_idx]

        values = stats.get_month_values(year)

        datasets.append({
            "label": str(year),
            "data": values,
            "backgroundColor": bg_color,
            "borderColor": border_color,
            "borderWidth": 1,
            "borderRadius": 4,
        })

    return {
        "labels": labels,
        "datasets": datasets,
        "unit_label": stats.unit_label,
    }


def format_monthly_value(value: float, unit_label: str) -> str:
    """Format a monthly value for display.

    Args:
        value: The numeric value.
        unit_label: Unit label (e.g., "EUR", "kg").

    Returns:
        Formatted string like "1,234 EUR" or "45.5 kg".
    """
    if unit_label.upper() in ("EUR", "USD", "GBP", "CHF"):
        # Currency - no decimals, thousands separator
        return f"{int(value):,} {unit_label}"
    else:
        # Other units - 1 decimal
        return f"{value:,.1f} {unit_label}"
