# Quantify Your Life

CLI tool to view statistics from multiple data sources, including the [Track & Graph](https://github.com/SamAmco/track-and-graph) Android app and Hometrainer exercise logs.

## Supported Data Sources

| Source | Description | Documentation |
|--------|-------------|---------------|
| **Track & Graph** | SQLite database from the [Track & Graph](https://github.com/SamAmco/track-and-graph) Android app | [docs/sources/track-and-graph.md](docs/sources/track-and-graph.md) |
| **Hometrainer** | Daily exercise distance logs stored as text files | [docs/sources/hometrainer.md](docs/sources/hometrainer.md) |
| **Git Stats** | Git repository analysis (lines added/removed, commits, projects created) | [docs/sources/git-stats.md](docs/sources/git-stats.md) |
| **Excel** | Excel files (.xls/.xlsx) with yearly tab structure | [docs/sources/excel.md](docs/sources/excel.md) |

## Features

- **Multiple data sources** - Track & Graph, Hometrainer logs, Git Stats, and Excel files
- **Multi-project support** - Separate configs for work, personal, etc. with shared global settings
- View statistics by **Group** (aggregated) or **Feature** (individual tracker)
- Arrow key navigation for easy selection
- **HTML Export** with charts for configured entries
- **Unit support** - Time (hours/minutes) and distance (km/mi)
- **Configurable display** - Custom number of years, YoY percentages, chart types and titles
- Comprehensive statistics:
  - Last 7 days / Last 31 days
  - Average per day (last 30 days, last 12 months, this year, last year)
  - Trend comparison vs previous 30 days
  - This week / This month / Last month / Last 12 months / Total
  - Configurable yearly totals with year-over-year comparisons

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

## Setup

1. Clone the repository

2. Copy the example config and configure your data sources:
   ```bash
   cp config_example.json config.json
   ```

3. Edit `config.json` with your data source paths (see [Multi-Project Support](#multi-project-support) for advanced setup):
   ```json
   {
       "sources": {
           "track_and_graph": {
               "db_path": "C:/path/to/your/track_and_graph.db"
           },
           "hometrainer": {
               "logs_path": "C:/path/to/Hometrainer_Logs",
               "unit": "km"
           }
       }
   }
   ```

   **Configuration options:**
   - `sources.track_and_graph.db_path` - Path to Track & Graph SQLite database
   - `sources.hometrainer.logs_path` - Path to Hometrainer logs directory
   - `sources.hometrainer.unit` - Display unit: `"km"` (default) or `"mi"`

   Only configure the sources you want to use. Unconfigured sources are ignored.

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

If multiple sources are configured, you'll be prompted to select one:
```
? Select data source:
> Track & Graph
  Hometrainer
```

### HTML Export

Export statistics to HTML files with interactive charts.

#### 1. Configure Export

**Windows:** Double-click `export-config.bat` or run:
```bash
uv run quantify-export-config
```

This opens an interactive menu where you can:
- **Add entry** - Select source, then groups/features to export
- **Remove entry** - Remove items from export list
- **Set export path** - Configure where HTML files are saved

Export configuration is stored in `config.json`:
```json
{
    "export": {
        "path": "C:/path/to/export/folder",
        "entries": [
            {"source": "track_and_graph", "type": "group", "id": 1},
            {"source": "track_and_graph", "type": "feature", "id": 10},
            {"source": "hometrainer", "type": "stats", "id": null}
        ]
    }
}
```

**Export entry options:**
- `source` - Data source ID (required)
- `type` - Entry type: `"group"`, `"feature"`, `"stats"`, `"top_features"` (required)
- `id` - Item ID, or `null` for sources with single stats (required)
- `title` - Custom page title (optional, defaults to item name)

Example with custom title:
```json
{"source": "excel", "type": "stats", "id": 1, "title": "Revenue Stats"}
```

#### 2. Run Export

**Windows:** Double-click `export.bat` or run:
```bash
uv run quantify-export
```

This generates HTML files with:
- Statistics table (same data as CLI)
- Bar chart visualization
- Dark theme styling

#### 3. Display Configuration (Optional)

Customize how statistics are displayed per source using the `display` object in source configuration:

```json
{
    "sources": {
        "excel": {
            "file_path": "C:/path/to/data.xlsx",
            "display": {
                "show_years": 7,
                "show_all_yoy": true,
                "chart": {
                    "type": "yearly",
                    "title": "Revenue by Year"
                }
            }
        }
    }
}
```

**Display options:**
- `show_years` - Number of years to display (default: 3)
- `show_all_yoy` - Show year-over-year percentage after every year (default: false)
- `hide_rows` - Array of row keys to hide (e.g., `["last_7_days", "this_week"]`)
- `show_rows` - Array of additional rows to show (e.g., `["yoy_this_vs_last"]`)

**Chart options:**
- `chart.type` - Chart type: `"periods"` (default) or `"yearly"`
  - `"periods"` - Shows Last 7d, This Week, This Month, Last Month, Last 31d
  - `"yearly"` - Shows yearly totals as bar chart
- `chart.title` - Custom chart title (auto-generated if not set)

## Multi-Project Support

Organize different configurations into separate projects, each with its own settings.

### Directory Structure

```
quantify-your-life/
  config.json              # Legacy: used if no projects/ folder exists
  projects/
    config.json            # Global/shared settings (optional)
    work/
      config.json          # Project-specific settings
    personal/
      config.json          # Project-specific settings
```

### How It Works

- **No `projects/` folder**: Uses root `config.json` (legacy behavior, unchanged)
- **`projects/` folder exists**: Shows interactive project selection menu
- **Global config** (`projects/config.json`): Shared settings inherited by all projects
- **Project config** (`projects/<name>/config.json`): Overrides global settings

### Configuration Merging

Project settings override global settings with deep merging:
- **Dictionaries**: Recursively merged (project values override global)
- **Arrays**: Replaced entirely (not merged)
- **Scalars**: Project value overrides global value

**Example global config** (`projects/config.json`):
```json
{
    "sources": {
        "git_stats": {
            "author": "Your Name",
            "root_paths": ["D:/GIT"]
        }
    }
}
```

**Example project config** (`projects/work/config.json`):
```json
{
    "sources": {
        "git_stats": {
            "root_paths": ["D:/GIT/Work"]
        }
    },
    "export": {
        "path": "D:/exports/work",
        "entries": [
            {"source": "git_stats", "type": "net", "id": null}
        ]
    }
}
```

**Result**: Work project uses author "Your Name" from global, but only scans `D:/GIT/Work`.

### CLI Options

```bash
# Interactive project selection (when projects/ exists)
uv run quantify

# Select project directly
uv run quantify --project work
uv run quantify -p personal

# List available projects
uv run quantify --list-projects
```

### Creating a New Project

1. **Via menu**: Select "Create new project..." when prompted
2. **Manually**: Create `projects/<name>/config.json` with your settings

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

### Adding a New Data Source

1. Create a new package under `src/quantify/sources/`
2. Implement `DataSource` abstract class from `sources/base.py`
3. Implement `DataProvider` protocol for your data format
4. Add configuration dataclass to `config/settings.py`
5. Register in `main.py`'s `_create_source_registry()`

## License

MIT
