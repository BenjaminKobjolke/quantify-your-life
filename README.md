# Quantify Your Life

CLI tool to view time statistics from the [Track & Graph](https://github.com/SamAmco/track-and-graph) Android app database.

## About Track & Graph

This tool reads the SQLite database exported from [Track & Graph](https://github.com/SamAmco/track-and-graph), a free and open-source Android app for tracking and visualizing personal data. Track & Graph allows you to log various metrics (time, counts, values) and create custom graphs to analyze your habits and patterns.

**Quantify Your Life** provides a quick CLI interface to view aggregated time statistics without needing to open the app.

## Features

- View statistics by **Group** (aggregated) or **Feature** (individual tracker)
- Arrow key navigation for easy selection
- **HTML Export** with charts for configured groups/features
- Comprehensive time statistics:
  - Last 7 days / Last 31 days
  - Average per day (last 30 days, last 12 months, this year, last year)
  - Trend comparison vs previous 30 days
  - This week / This month / Last month / Last 12 months / Total

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

## Setup

1. Clone the repository

2. Copy the example config and set your database path:
   ```bash
   cp config_example.json config.json
   ```

3. Edit `config.json` with your Track & Graph database path:
   ```json
   {
       "db_path": "C:/path/to/your/track_and_graph.db"
   }
   ```

4. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

### View Statistics (CLI)

**Windows:** Double-click `start.bat` or run:
```bash
uv run quantify
```

**Linux/macOS:**
```bash
uv run quantify
```

### HTML Export

Export statistics to HTML files with interactive charts.

#### 1. Configure Export

**Windows:** Double-click `export-config.bat` or run:
```bash
uv run quantify-export-config
```

This opens an interactive menu where you can:
- **Add entry** - Select groups or features to export
- **Remove entry** - Remove items from export list
- **Set export path** - Configure where HTML files are saved

#### 2. Run Export

**Windows:** Double-click `export.bat` or run:
```bash
uv run quantify-export
```

This generates HTML files with:
- Statistics table (same data as CLI)
- Bar chart visualization
- Dark theme styling

## Example Output

```
? How would you like to view statistics? By Feature
? Select a feature: Exercise

        Statistics for: Exercise
┌─────────────────────────────┬──────────┐
│ Period                      │     Time │
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

## Development

### Run linting
```bash
uv run ruff check src/
```

### Run type checking
```bash
uv run mypy src/
```

### Run tests
```bash
uv run pytest
```

## License

MIT
