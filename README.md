# Quantify Your Life

CLI tool to view statistics from multiple data sources, including the [Track & Graph](https://github.com/SamAmco/track-and-graph) Android app and Hometrainer exercise logs.

## Supported Data Sources

### Track & Graph

Reads the SQLite database exported from [Track & Graph](https://github.com/SamAmco/track-and-graph), a free and open-source Android app for tracking and visualizing personal data. Track & Graph allows you to log various metrics (time, counts, values) and create custom graphs to analyze your habits and patterns.

### Hometrainer

Reads daily exercise logs stored as text files. Each file contains a single distance value (in miles) for that day.

**Log format:**
- Location: `{logs_path}/{YYYY}/{YYYY_MM_DD}.txt`
- Content: Single float value (e.g., `5.2`)
- Example: `Hometrainer_Logs/2024/2024_01_15.txt` containing `8.5`

### Git Stats

Analyzes git repositories to track lines added, removed, and commits over time. Scans all repositories under configured root paths and caches results for fast subsequent queries.

**Tracked metrics:**
- Lines Added / Removed / Net
- Commits
- Projects Created (first commit date)

**Default exclusions** (to focus on meaningful code changes):

| Category | Excluded | Reason |
|----------|----------|--------|
| **Directories** | `node_modules`, `vendor`, `venv`, `.venv`, `target`, `build`, `dist`, `bin`, `obj` | Dependencies and build output |
| | `Library`, `Temp`, `Logs` | Unity project cache |
| | `.idea`, `.vscode`, `.vs` | IDE configuration |
| | `__pycache__`, `.pytest_cache`, `.mypy_cache` | Python cache |
| **Extensions** | `.json`, `.xml`, `.yaml`, `.yml`, `.toml` | Config files (often auto-generated) |
| | `.md`, `.txt`, `.rst` | Documentation |
| | `.css`, `.scss`, `.html` | Styling/markup |
| | `.png`, `.jpg`, `.svg`, `.pdf` | Media assets |
| | `.lock`, `.map` | Generated files |
| | `.meta` | Unity metadata |
| **Filenames** | `package-lock.json`, `yarn.lock`, `poetry.lock`, etc. | Lock files |
| | `.gitignore`, `.editorconfig` | Config files |

**Customizing exclusions** in `config.json`:
```json
{
    "sources": {
        "git_stats": {
            "author": "Your Name",
            "root_paths": ["D:/projects"],
            "exclude_dirs": ["node_modules", "custom_dir"],
            "exclude_extensions": [".json", ".custom"],
            "exclude_filenames": ["package-lock.json"]
        }
    }
}
```

Note: Custom lists replace the defaults entirely. Use the Debug Git Exclusions menu to see what files are being counted in each repository.

## Features

- **Multiple data sources** - Track & Graph, Hometrainer logs, and Git Stats
- **Multi-project support** - Separate configs for work, personal, etc. with shared global settings
- View statistics by **Group** (aggregated) or **Feature** (individual tracker)
- Arrow key navigation for easy selection
- **HTML Export** with charts for configured entries
- **Unit support** - Time (hours/minutes) and distance (km/mi)
- Comprehensive statistics:
  - Last 7 days / Last 31 days
  - Average per day (last 30 days, last 12 months, this year, last year)
  - Trend comparison vs previous 30 days
  - This week / This month / Last month / Last 12 months / Total

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

#### 2. Run Export

**Windows:** Double-click `export.bat` or run:
```bash
uv run quantify-export
```

This generates HTML files with:
- Statistics table (same data as CLI)
- Bar chart visualization
- Dark theme styling

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

## Example Output

### Track & Graph (Time)

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

### Hometrainer (Distance)

```
? Select data source: Hometrainer

     Statistics for: Hometrainer (km)
┌─────────────────────────────┬──────────┐
│ Period                      │    Value │
├─────────────────────────────┼──────────┤
│ Last 7 days                 │  42.5 km │
│ Last 31 days                │ 185.2 km │
│                             │          │
│ Avg/day (last 30 days)      │   6.2 km │
│ vs previous 30 days         │   +8.3%  │
│                             │          │
│ ...                         │      ... │
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

## Test SQL
sqlite3 "C:\Users\USERNAME\.quantify-your-life\git_stats_cache.db" "SELECT repo_path, date, added, removed, commits FROM daily_stats WHERE repo_path LIKE '%quantify-your-life%' ORDER BY date DESC
LIMIT 20"

## License

MIT
