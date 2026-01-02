"""CLI handlers for different data sources."""

from quantify.cli.handlers.git_stats import GitStatsHandler
from quantify.cli.handlers.hometrainer import handle_hometrainer
from quantify.cli.handlers.track_and_graph import TrackAndGraphHandler, handle_track_and_graph

__all__ = [
    "GitStatsHandler",
    "TrackAndGraphHandler",
    "handle_track_and_graph",
    "handle_hometrainer",
]
