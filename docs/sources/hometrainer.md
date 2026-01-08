# Hometrainer Data Source

Reads daily exercise logs stored as text files, tracking distance traveled on exercise equipment.

## Overview

The Hometrainer data source provides simple distance tracking by reading daily log files. Each file contains a single distance value for that day.

## Configuration

```json
{
    "sources": {
        "hometrainer": {
            "logs_path": "C:/path/to/Hometrainer_Logs",
            "unit": "km"
        }
    }
}
```

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `logs_path` | string | Yes | - | Path to the directory containing log files |
| `unit` | string | No | `"km"` | Display unit: `"km"` or `"mi"` |

## Log File Format

### Directory Structure

```
Hometrainer_Logs/
  2024/
    2024_01_01.txt
    2024_01_02.txt
    ...
  2025/
    2025_01_01.txt
    ...
```

### File Format

- **Location**: `{logs_path}/{YYYY}/{YYYY_MM_DD}.txt`
- **Content**: Single float value representing distance in **miles**
- **Example**: `2024/2024_01_15.txt` containing `8.5`

### Important Notes

- Log files store values in **miles** internally
- Values are converted to the configured display unit (km or mi)
- Conversion factor: 1 mile = 1.60934 km

## Available Statistics

| Period | Description |
|--------|-------------|
| Last 7 days | Total distance in the past week |
| Last 31 days | Total distance in the past month |
| Avg/day (last 30 days) | Daily average over the past 30 days |
| vs previous 30 days | Trend comparison (percentage change) |
| Avg/day (last 12 months) | Daily average over the past year |
| Avg/day (this year) | Daily average since January 1st |
| Avg/day (last year) | Daily average for the previous calendar year |
| This week | Total from Monday to today |
| This month | Total from the 1st to today |
| Last month | Total for the previous calendar month |
| Last 12 months | Total over the past 365 days |
| Total | All-time total distance |

## Export Configuration

To export Hometrainer statistics to HTML:

```json
{
    "export": {
        "entries": [
            {"source": "hometrainer", "type": "stats", "id": null}
        ]
    }
}
```

## Example Output

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
│ vs previous 30 days         │    +8.3% │
│                             │          │
│ Avg/day (last 12 months)    │   5.8 km │
│ Avg/day (this year)         │   6.1 km │
│ Avg/day (last year)         │   5.2 km │
│                             │          │
│ This week                   │  18.5 km │
│ This month                  │  85.3 km │
│ Last month                  │ 156.2 km │
│ Last 12 months              │2115.6 km │
│ Total                       │3250.8 km │
└─────────────────────────────┴──────────┘
```

## Creating Log Files

To add a new log entry:

1. Navigate to your logs directory
2. Create the year folder if it doesn't exist (e.g., `2025/`)
3. Create a text file with the date format `YYYY_MM_DD.txt`
4. Enter the distance value in miles as a single number

Example:
```bash
# Create log for January 8, 2025 with 5.2 miles
echo 5.2 > Hometrainer_Logs/2025/2025_01_08.txt
```
