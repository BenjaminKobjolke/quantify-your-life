# Git Stats Data Source

Analyzes git repositories to track coding activity including lines added, removed, and commits over time.

## Overview

Git Stats scans all repositories under configured root paths and provides statistics on your coding activity. It uses caching for fast subsequent queries and supports project-type-specific filtering to focus on meaningful code changes.

## Configuration

```json
{
    "sources": {
        "git_stats": {
            "author": "Your Name",
            "root_paths": ["D:/projects", "D:/work"],
            "exclude_dirs": ["node_modules", "vendor"],
            "exclude_extensions": [".json", ".lock"],
            "exclude_filenames": ["package-lock.json"]
        }
    }
}
```

### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `author` | string | Yes | Git author name to filter commits |
| `root_paths` | array | Yes | Directories containing git repositories |
| `exclude_dirs` | array | No | Directories to exclude (replaces defaults) |
| `exclude_extensions` | array | No | File extensions to exclude (replaces defaults) |
| `exclude_filenames` | array | No | Specific filenames to exclude (replaces defaults) |

## Tracked Metrics

| Metric | Description |
|--------|-------------|
| **Lines Added** | Total lines added by the author |
| **Lines Removed** | Total lines removed by the author |
| **Net Lines** | Net change (added - removed) |
| **Commits** | Number of commits by the author |
| **Projects Created** | Repositories where first commit falls in the period |

## Default Exclusions

To focus on meaningful code changes, the following are excluded by default:

### Directories

| Category | Excluded |
|----------|----------|
| **Dependencies** | `node_modules`, `vendor`, `venv`, `.venv`, `env`, `target`, `build`, `dist`, `bin`, `obj` |
| **Unity Cache** | `Library`, `Temp`, `Logs` |
| **IDE Config** | `.idea`, `.vscode`, `.vs` |
| **Python Cache** | `__pycache__`, `.pytest_cache`, `.mypy_cache` |
| **Other** | `.git`, `.svn`, `coverage`, `.tox`, `.eggs` |

### File Extensions

| Category | Excluded |
|----------|----------|
| **Config** | `.json`, `.xml`, `.yaml`, `.yml`, `.toml` |
| **Documentation** | `.md`, `.txt`, `.rst` |
| **Styling** | `.css`, `.scss`, `.html` |
| **Media** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.pdf`, `.ico` |
| **Generated** | `.lock`, `.map`, `.min.js`, `.min.css`, `.d.ts` |
| **Unity** | `.meta` |
| **Flutter** | `.g.dart`, `.freezed.dart` |

### Specific Filenames

- `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
- `poetry.lock`, `Pipfile.lock`, `Cargo.lock`
- `composer.lock`, `Gemfile.lock`
- `.gitignore`, `.editorconfig`, `.gitattributes`

## Project Type Detection

Git Stats automatically detects project types and applies appropriate filtering rules.

### Supported Project Types

| Type | Detection | Include Patterns |
|------|-----------|------------------|
| **Unity** | `*.sln` + `Assets/` + `ProjectSettings/` | `Assets/Scripts/**/*.cs`, `Assets/**/*.cs` |
| **Flutter** | `pubspec.yaml` | `lib/**/*.dart` |
| **Python** | `pyproject.toml`, `setup.py`, `requirements.txt` | Global exclusions |
| **Node** | `package.json` | Global exclusions |
| **Arduino** | `platformio.ini` or `*.ino` files | `src/**/*`, `*.ino`, `*.cpp`, `*.c`, `*.h` |
| **Go** | `go.mod` | Global exclusions |
| **Rust** | `Cargo.toml` | Global exclusions |
| **Generic** | Default fallback | Global exclusions |

### Manual Project Type Assignment

Use the Debug Git Exclusions menu to:
- View which files are counted/excluded for each repository
- Manually assign project types for ambiguous repositories
- Clear cached data when project type changes

## Caching

Git Stats uses SQLite caching for performance:

- **Cache Location**: `~/.quantify-your-life/git_stats_cache.db`
- **Today's data is never cached** (commits may still be added)
- **In-memory session cache** prevents re-querying git within the same process
- Cache stores daily stats and repository metadata (project types)

### Cache Management

- Cache is automatically invalidated when project type changes
- Use "Clear repo cache" in the debug menu to force refresh
- Empty results are cached to avoid re-querying empty repos

## Analysis Features

### Top Repositories

View the top 10 repositories by net lines changed for any time period.

### Projects Created

Track how many new projects you started in each time period (based on first commit date).

### Commits by Repository

See commit counts broken down by repository for detailed activity analysis.

### Exclusion Analysis

The debug menu shows exactly which files are being counted or excluded for each repository, including the reason for exclusion.

## Export Configuration

```json
{
    "export": {
        "entries": [
            {"source": "git_stats", "type": "added", "id": null},
            {"source": "git_stats", "type": "removed", "id": null},
            {"source": "git_stats", "type": "net", "id": null},
            {"source": "git_stats", "type": "commits", "id": null},
            {"source": "git_stats", "type": "projects_created", "id": null}
        ]
    }
}
```

### Entry Types

| Type | Description |
|------|-------------|
| `added` | Lines added statistics |
| `removed` | Lines removed statistics |
| `net` | Net lines (added - removed) statistics |
| `commits` | Commit count statistics |
| `projects_created` | New projects count statistics |

## Available Statistics

| Period | Description |
|--------|-------------|
| Last 7 days | Activity in the past week |
| Last 31 days | Activity in the past month |
| Avg/day (last 30 days) | Daily average over the past 30 days |
| vs previous 30 days | Trend comparison (percentage change) |
| Avg/day (last 12 months) | Daily average over the past year |
| Avg/day (this year) | Daily average since January 1st |
| Avg/day (last year) | Daily average for the previous calendar year |
| This week | Activity from Monday to today |
| This month | Activity from the 1st to today |
| Last month | Activity for the previous calendar month |
| Last 12 months | Activity over the past 365 days |
| Total | All-time activity |

## Performance

- Uses parallel processing (8 worker threads) for multi-repo analysis
- Progress indicator shows scanning status
- Caching significantly speeds up repeated queries

## Repository Discovery

Git Stats scans **one level deep** in each root path for `.git` directories. Nested repositories are not automatically discovered.

```
root_paths: ["D:/projects"]

D:/projects/
  repo1/.git     # Found
  repo2/.git     # Found
  folder/
    repo3/.git   # NOT found (nested too deep)
```

## Debugging

Use the Debug Git Exclusions menu to troubleshoot:

1. Select a repository to analyze
2. View counted vs excluded files
3. See exclusion reasons for each file
4. Detect or manually set project type
5. Clear cache if needed

## Example SQL Query

To inspect cached data directly:

```sql
sqlite3 "~/.quantify-your-life/git_stats_cache.db" \
  "SELECT repo_path, date, added, removed, commits
   FROM daily_stats
   WHERE repo_path LIKE '%project-name%'
   ORDER BY date DESC
   LIMIT 20"
```
