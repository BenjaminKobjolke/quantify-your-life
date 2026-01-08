# Track & Graph Data Source

Reads the SQLite database exported from [Track & Graph](https://github.com/SamAmco/track-and-graph), a free and open-source Android app for tracking and visualizing personal data.

## Overview

Track & Graph allows you to log various metrics (time, counts, values) and create custom graphs to analyze your habits and patterns. This data source reads the exported database and provides statistics on your tracked data.

## Configuration

```json
{
    "sources": {
        "track_and_graph": {
            "db_path": "C:/path/to/your/track_and_graph.db"
        }
    }
}
```

### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `db_path` | string | Yes | Path to the Track & Graph SQLite database file |

## Data Organization

Track & Graph organizes data hierarchically:

- **Groups**: Aggregations of multiple features (e.g., "Health", "Productivity")
- **Features**: Individual trackers within groups (e.g., "Exercise", "Sleep")

## Available Statistics

When viewing statistics, you can choose:
- **By Group**: Aggregated statistics across all features in a group
- **By Feature**: Statistics for a single tracker

### Statistics Provided

| Period | Description |
|--------|-------------|
| Last 7 days | Sum of values in the past week |
| Last 31 days | Sum of values in the past month |
| Avg/day (last 30 days) | Daily average over the past 30 days |
| vs previous 30 days | Trend comparison (percentage change) |
| Avg/day (last 12 months) | Daily average over the past year |
| Avg/day (this year) | Daily average since January 1st |
| Avg/day (last year) | Daily average for the previous calendar year |
| This week | Sum from Monday to today |
| This month | Sum from the 1st to today |
| Last month | Sum for the previous calendar month |
| Last 12 months | Sum over the past 365 days |
| Total | All-time sum |

## Features

### Top Features in Group

When viewing group statistics, the tool shows the **Top 10 features** by value within that group for the selected time period. This helps identify which trackers contribute most to your totals.

### Unit Support

Track & Graph features support time-based units. Values stored in seconds are automatically converted to hours and minutes for display (e.g., "5h 23m").

## Export Configuration

To export Track & Graph statistics to HTML:

```json
{
    "export": {
        "entries": [
            {"source": "track_and_graph", "type": "group", "id": 1},
            {"source": "track_and_graph", "type": "feature", "id": 10}
        ]
    }
}
```

### Entry Types

| Type | Description |
|------|-------------|
| `group` | Export aggregated group statistics |
| `feature` | Export individual feature statistics |

## Example Output

```
? Select data source: Track & Graph
? How would you like to view statistics? By Feature
? Select a feature: Exercise

        Statistics for: Exercise
┌─────────────────────────────┬──────────┐
│ Period                      │    Value │
├─────────────────────────────┼──────────┤
│ Last 7 days                 │   5h 23m │
│ Last 31 days                │  22h 15m │
│                             │          │
│ Avg/day (last 30 days)      │      45m │
│ vs previous 30 days         │   +15.2% │
│                             │          │
│ Avg/day (last 12 months)    │      38m │
│ Avg/day (this year)         │      42m │
│ Avg/day (last year)         │      35m │
│                             │          │
│ This week                   │   2h 30m │
│ This month                  │   8h 45m │
│ Last month                  │  12h 20m │
│ Last 12 months              │ 230h 15m │
│ Total                       │ 450h 30m │
└─────────────────────────────┴──────────┘
```

## Backwards Compatibility

The old config format with `db_path` at the root level is still supported:

```json
{
    "db_path": "C:/path/to/track_and_graph.db"
}
```

This is automatically converted to the new format internally.
