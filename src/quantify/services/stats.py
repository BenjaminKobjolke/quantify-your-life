"""Statistics calculation service."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from quantify.db.repositories.datapoints import DataPointsRepository
from quantify.db.repositories.features import FeaturesRepository


@dataclass
class TimeStats:
    """Time statistics for a feature or group."""

    # Recent periods
    last_7_days: float
    last_31_days: float

    # Averages
    avg_per_day_last_30_days: float
    trend_vs_previous_30_days: float | None  # Percentage, None if no previous data
    avg_per_day_last_12_months: float
    avg_per_day_this_year: float
    avg_per_day_last_year: float

    # Standard periods
    this_week: float
    this_month: float
    last_month: float
    last_12_months: float
    total: float


class StatsService:
    """Service for calculating time statistics."""

    def __init__(
        self,
        datapoints_repo: DataPointsRepository,
        features_repo: FeaturesRepository,
    ) -> None:
        """Initialize stats service.

        Args:
            datapoints_repo: Repository for data points.
            features_repo: Repository for features.
        """
        self._datapoints = datapoints_repo
        self._features = features_repo

    def get_feature_stats(self, feature_id: int) -> TimeStats:
        """Get time statistics for a single feature.

        Args:
            feature_id: The feature ID to get stats for.

        Returns:
            TimeStats with all time periods.
        """
        ranges = self._get_time_ranges()
        get_sum = self._datapoints.get_sum_by_feature

        # Recent periods
        last_7_days = get_sum(feature_id, ranges["7_days_ago"], ranges["now"])
        last_31_days = get_sum(feature_id, ranges["31_days_ago"], ranges["now"])

        # Last 30 days and previous 30 days for trend
        last_30_days = get_sum(feature_id, ranges["30_days_ago"], ranges["now"])
        previous_30_days = get_sum(feature_id, ranges["60_days_ago"], ranges["30_days_ago"])

        # Averages
        avg_last_30 = last_30_days / 30
        trend = self._calculate_trend(last_30_days, previous_30_days)

        last_12_months_sum = get_sum(feature_id, ranges["12_months_ago"], ranges["now"])
        avg_last_12_months = last_12_months_sum / 365

        this_year_sum = get_sum(feature_id, ranges["this_year_start"], ranges["now"])
        days_this_year = ranges["days_this_year"]
        avg_this_year = this_year_sum / days_this_year if days_this_year > 0 else 0

        last_year_sum = get_sum(feature_id, ranges["last_year_start"], ranges["last_year_end"])
        avg_last_year = last_year_sum / 365

        return TimeStats(
            last_7_days=last_7_days,
            last_31_days=last_31_days,
            avg_per_day_last_30_days=avg_last_30,
            trend_vs_previous_30_days=trend,
            avg_per_day_last_12_months=avg_last_12_months,
            avg_per_day_this_year=avg_this_year,
            avg_per_day_last_year=avg_last_year,
            this_week=get_sum(feature_id, ranges["week_start"], ranges["now"]),
            this_month=get_sum(feature_id, ranges["month_start"], ranges["now"]),
            last_month=get_sum(feature_id, ranges["last_month_start"], ranges["last_month_end"]),
            last_12_months=last_12_months_sum,
            total=get_sum(feature_id),
        )

    def get_group_stats(self, group_id: int) -> TimeStats:
        """Get aggregated time statistics for all features in a group.

        Args:
            group_id: The group ID to get stats for.

        Returns:
            TimeStats with all time periods aggregated across features.
        """
        features = self._features.get_by_group_id(group_id)
        feature_ids = [f.id for f in features]

        if not feature_ids:
            return TimeStats(
                last_7_days=0.0,
                last_31_days=0.0,
                avg_per_day_last_30_days=0.0,
                trend_vs_previous_30_days=None,
                avg_per_day_last_12_months=0.0,
                avg_per_day_this_year=0.0,
                avg_per_day_last_year=0.0,
                this_week=0.0,
                this_month=0.0,
                last_month=0.0,
                last_12_months=0.0,
                total=0.0,
            )

        ranges = self._get_time_ranges()
        get_sum = self._datapoints.get_sum_by_features

        # Recent periods
        last_7_days = get_sum(feature_ids, ranges["7_days_ago"], ranges["now"])
        last_31_days = get_sum(feature_ids, ranges["31_days_ago"], ranges["now"])

        # Last 30 days and previous 30 days for trend
        last_30_days = get_sum(feature_ids, ranges["30_days_ago"], ranges["now"])
        previous_30_days = get_sum(feature_ids, ranges["60_days_ago"], ranges["30_days_ago"])

        # Averages
        avg_last_30 = last_30_days / 30
        trend = self._calculate_trend(last_30_days, previous_30_days)

        last_12_months_sum = get_sum(feature_ids, ranges["12_months_ago"], ranges["now"])
        avg_last_12_months = last_12_months_sum / 365

        this_year_sum = get_sum(feature_ids, ranges["this_year_start"], ranges["now"])
        days_this_year = ranges["days_this_year"]
        avg_this_year = this_year_sum / days_this_year if days_this_year > 0 else 0

        last_year_sum = get_sum(feature_ids, ranges["last_year_start"], ranges["last_year_end"])
        avg_last_year = last_year_sum / 365

        return TimeStats(
            last_7_days=last_7_days,
            last_31_days=last_31_days,
            avg_per_day_last_30_days=avg_last_30,
            trend_vs_previous_30_days=trend,
            avg_per_day_last_12_months=avg_last_12_months,
            avg_per_day_this_year=avg_this_year,
            avg_per_day_last_year=avg_last_year,
            this_week=get_sum(feature_ids, ranges["week_start"], ranges["now"]),
            this_month=get_sum(feature_ids, ranges["month_start"], ranges["now"]),
            last_month=get_sum(
                feature_ids, ranges["last_month_start"], ranges["last_month_end"]
            ),
            last_12_months=last_12_months_sum,
            total=get_sum(feature_ids),
        )

    def _calculate_trend(self, current: float, previous: float) -> float | None:
        """Calculate percentage change between two periods.

        Args:
            current: Current period value.
            previous: Previous period value.

        Returns:
            Percentage change or None if previous is zero.
        """
        if previous <= 0:
            return None
        return ((current - previous) / previous) * 100

    def _get_time_ranges(self) -> dict[str, int]:
        """Calculate time ranges for statistics.

        Returns:
            Dictionary with epoch_milli values for various time boundaries.
        """
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Recent day ranges
        days_7_ago = today_start - timedelta(days=7)
        days_30_ago = today_start - timedelta(days=30)
        days_31_ago = today_start - timedelta(days=31)
        days_60_ago = today_start - timedelta(days=60)

        # Start of this week (Monday 00:00)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # Start of this month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Last month boundaries
        last_month_end = month_start - timedelta(seconds=1)
        last_month_start = last_month_end.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # 12 months ago
        months_12_ago = today_start - timedelta(days=365)

        # This year
        this_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        days_this_year = (now - this_year_start).days + 1

        # Last year
        last_year_start = this_year_start.replace(year=this_year_start.year - 1)
        last_year_end = this_year_start - timedelta(seconds=1)

        return {
            "now": int(now.timestamp() * 1000),
            "7_days_ago": int(days_7_ago.timestamp() * 1000),
            "30_days_ago": int(days_30_ago.timestamp() * 1000),
            "31_days_ago": int(days_31_ago.timestamp() * 1000),
            "60_days_ago": int(days_60_ago.timestamp() * 1000),
            "week_start": int(week_start.timestamp() * 1000),
            "month_start": int(month_start.timestamp() * 1000),
            "last_month_start": int(last_month_start.timestamp() * 1000),
            "last_month_end": int(last_month_end.timestamp() * 1000),
            "12_months_ago": int(months_12_ago.timestamp() * 1000),
            "this_year_start": int(this_year_start.timestamp() * 1000),
            "last_year_start": int(last_year_start.timestamp() * 1000),
            "last_year_end": int(last_year_end.timestamp() * 1000),
            "days_this_year": days_this_year,
        }


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string like "5h 23m" or "45m" or "0m".
    """
    if seconds <= 0:
        return "0m"

    total_minutes = int(seconds / 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def format_trend(percentage: float | None) -> str:
    """Format trend percentage.

    Args:
        percentage: Percentage change or None.

    Returns:
        Formatted string like "+15.2%" or "-8.3%" or "N/A".
    """
    if percentage is None:
        return "N/A"
    sign = "+" if percentage >= 0 else ""
    return f"{sign}{percentage:.1f}%"
