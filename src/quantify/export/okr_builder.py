"""OKR line chart data builder for HTML export."""

from datetime import datetime, timedelta

from quantify.services.okr_stats import OkrStats

# Color palette for KR lines
KR_COLORS = [
    ("rgba(0, 212, 255, 1)", "rgba(0, 212, 255, 0.1)"),  # Cyan
    ("rgba(255, 159, 64, 1)", "rgba(255, 159, 64, 0.1)"),  # Orange
    ("rgba(153, 102, 255, 1)", "rgba(153, 102, 255, 0.1)"),  # Purple
    ("rgba(75, 192, 192, 1)", "rgba(75, 192, 192, 0.1)"),  # Teal
    ("rgba(255, 99, 132, 1)", "rgba(255, 99, 132, 0.1)"),  # Pink
    ("rgba(255, 205, 86, 1)", "rgba(255, 205, 86, 0.1)"),  # Yellow
    ("rgba(54, 162, 235, 1)", "rgba(54, 162, 235, 0.1)"),  # Blue
]


def build_okr_chart_data(stats: OkrStats) -> dict:
    """Build Chart.js line chart data from OkrStats.

    Includes prognosis (dashed) datasets projected to target_date when available.

    Args:
        stats: OKR statistics with Key Results.

    Returns:
        Dict with:
            - labels: List of date strings for X-axis
            - datasets: List of dataset dicts for Chart.js line chart
    """
    if not stats.key_results or not stats.key_results[0].data_points:
        return {"labels": [], "datasets": []}

    # Collect all actual dates from first KR (all KRs share same dates)
    actual_dates: list[datetime] = [dp[0] for dp in stats.key_results[0].data_points]
    num_actual = len(actual_dates)

    # Generate future weekly dates for prognosis if target_date is set
    future_dates: list[datetime] = []
    if stats.target_date and actual_dates:
        last_date = actual_dates[-1]
        current = last_date + timedelta(days=7)
        while current <= stats.target_date:
            future_dates.append(current)
            current += timedelta(days=7)
        # Include the target date itself if not already included
        if future_dates and future_dates[-1] < stats.target_date:
            future_dates.append(stats.target_date)
        elif not future_dates and last_date < stats.target_date:
            future_dates.append(stats.target_date)

    all_dates = actual_dates + future_dates
    labels = [d.strftime("%d.%m") for d in all_dates]

    datasets = []
    for idx, kr in enumerate(stats.key_results):
        color_idx = idx % len(KR_COLORS)
        border_color, bg_color = KR_COLORS[color_idx]

        # Actual data values, padded with None for future dates
        actual_values: list[float | None] = [dp[1] for dp in kr.data_points]
        actual_values += [None] * len(future_dates)

        datasets.append({
            "label": kr.name,
            "data": actual_values,
            "borderColor": border_color,
            "backgroundColor": bg_color,
            "fill": False,
            "tension": 0.2,
            "pointRadius": 4,
            "pointHoverRadius": 6,
            "borderWidth": 2,
        })

        # Prognosis dataset (only if we have future dates and actual data)
        if future_dates and kr.data_points:
            last_pct = kr.data_points[-1][1]
            num_points = len(kr.data_points)

            # Average weekly progress rate
            avg_weekly = last_pct / num_points if num_points > 0 else 0

            # Build prognosis values: null for all actual dates except last,
            # then projected values for future dates
            prognosis_values: list[float | None] = [None] * (num_actual - 1)
            # Connect to last actual point
            prognosis_values.append(last_pct)

            for week_idx, _date in enumerate(future_dates, start=1):
                projected = last_pct + avg_weekly * week_idx
                prognosis_values.append(min(projected, 100.0))

            datasets.append({
                "label": kr.name + " (Prognose)",
                "data": prognosis_values,
                "borderColor": border_color,
                "backgroundColor": "transparent",
                "fill": False,
                "tension": 0.2,
                "pointRadius": 0,
                "pointHoverRadius": 4,
                "borderWidth": 2,
                "borderDash": [8, 4],
            })

    return {
        "labels": labels,
        "datasets": datasets,
    }
