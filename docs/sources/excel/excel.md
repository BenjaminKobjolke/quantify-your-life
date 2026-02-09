# Excel Data Source

Reads data from Excel files (.xls and .xlsx) with yearly tab structure, providing aggregated statistics per year.

## Overview

The Excel data source reads values from specified columns in Excel files, where each tab represents a year. It supports custom column ranges per tab, allowing flexibility when spreadsheet structure changes over time.

## Configuration

```json
{
    "sources": {
        "excel": {
            "sources": [
                {
                    "name": "Savings",
                    "file_path": "C:/path/to/finances.xlsx",
                    "tabs": {
                        "2020": "K2:K",
                        "2021": "K2:K",
                        "2022": "K2:K",
                        "2023": "L2:L",
                        "2024": "L2:L",
                        "2025": "L2:L"
                    },
                    "function": "sum",
                    "unit_label": "EUR"
                }
            ]
        }
    }
}
```

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `name` | string | Yes | - | Display name for the source |
| `file_path` | string | Yes | - | Path to the Excel file (.xls or .xlsx) |
| `tabs` | object | Yes | - | Object mapping tab names (years) to column ranges |
| `function` | string | No | `"sum"` | Aggregation function (currently only "sum") |
| `unit_label` | string | No | `""` | Optional unit label for display (e.g., "EUR", "kg") |
| `display` | object | No | `null` | Display configuration for stats output |
| `date_column` | string | No | `null` | Column range for dates (e.g., "D3:D") - enables monthly comparison |

### Display Configuration

The `display` option allows customizing which statistics rows are shown in the output. This is especially useful for Excel sources where daily/weekly stats are not meaningful.

```json
{
    "name": "Invoices",
    "file_path": "...",
    "tabs": {"2024": "K3:K", "2025": "K3:K"},
    "display": {
        "hide_rows": ["last_7_days", "last_31_days", "this_week", "this_month", "last_month"],
        "show_years": 5,
        "show_all_yoy": true
    }
}
```

#### Display Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `hide_rows` | array | `[]` | List of row keys to hide from output |
| `show_rows` | array | `[]` | List of extra row keys to show (e.g., YoY percentages) |
| `show_years` | integer | `3` | Number of years to display (e.g., 5 shows current year + 4 previous) |
| `show_all_yoy` | boolean | `false` | Show YoY percentage after every year automatically |

#### Available Row Keys

**Default rows (can be hidden):**
- `last_7_days`, `last_31_days` - Recent period totals
- `avg_per_day_last_30_days`, `trend_vs_previous_30_days` - 30-day averages
- `avg_per_day_last_12_months`, `avg_per_day_this_year`, `avg_per_day_last_year` - Annual averages
- `total_this_year`, `total_last_year`, `total_year_before` - Yearly totals (first 3 years)
- `total_year_{YEAR}` - Additional yearly totals when `show_years > 3` (e.g., `total_year_2022`)
- `this_week`, `this_month`, `last_month`, `last_12_months`, `total` - Standard periods

**Extra rows (can be shown):**
- `yoy_this_vs_last` - Year-over-year percentage: this year vs last year
- `yoy_last_vs_year_before` - Year-over-year percentage: last year vs year before
- `yoy_{YEAR}` - Additional YoY percentages when `show_years > 3` (e.g., `yoy_2023` for 2023 vs 2022)

### Tabs Configuration

The `tabs` field is an object where:
- Keys are tab/sheet names (typically years like "2024", "2025")
- Values are column ranges in the format `COLUMN_START:COLUMN_END`

#### Column Range Format

| Format | Description |
|--------|-------------|
| `K2:K` | Column K from row 2 to the last row with data |
| `K2:K100` | Column K from row 2 to row 100 |
| `AB5:AB` | Column AB from row 5 to the last row with data |

Each tab can have a different column range, useful when spreadsheet structure changes between years.

## Multiple Excel Sources

You can configure multiple Excel sources by adding more entries to the `sources` array:

```json
{
    "sources": {
        "excel": {
            "sources": [
                {
                    "name": "Savings",
                    "file_path": "C:/finances.xlsx",
                    "tabs": {"2024": "K2:K", "2025": "K2:K"},
                    "unit_label": "EUR"
                },
                {
                    "name": "Weight",
                    "file_path": "C:/health.xlsx",
                    "tabs": {"2024": "B2:B", "2025": "B2:B"},
                    "unit_label": "kg"
                }
            ]
        }
    }
}
```

Each source appears as a separate selectable item in the menu.

## File Format Support

| Format | Extension | Library |
|--------|-----------|---------|
| Excel 2007+ | `.xlsx` | pyexcel-xlsx |
| Excel 97-2003 | `.xls` | pyexcel-xls |

Both formats are automatically detected based on file extension.

## Statistics

Since Excel sources only have yearly totals (one sum per tab/year), the following statistics are meaningful:

| Period | Description |
|--------|-------------|
| This year | Sum from the current year's tab |
| Last year | Sum from the previous year's tab |
| Total | Sum of all configured years |

**Note**: Daily, weekly, and monthly statistics will show the full year's value since the data is aggregated annually.

## Export Configuration

To export Excel statistics to HTML:

```json
{
    "export": {
        "entries": [
            {"source": "excel", "type": "stats", "id": null}
        ]
    }
}
```

For multiple Excel sources, use the source ID:
- First source: `"excel"`
- Second source: `"excel_1"`
- Third source: `"excel_2"`
- etc.

## Monthly Comparison

When `date_column` is configured, you can export a monthly year-over-year comparison chart that groups values by month and compares across years.

### Configuration

```json
{
    "name": "Revenue",
    "file_path": "C:/finances.xlsx",
    "tabs": {
        "2024": "K3:K",
        "2025": "K3:K"
    },
    "date_column": "D3:D",
    "unit_label": "EUR"
}
```

The `date_column` should contain dates in DD.MM.YYYY format (e.g., "12.01.2026"). Each row's date determines which month the value belongs to.

### Export Configuration

To export the monthly comparison chart:

```json
{
    "export": {
        "entries": [
            {"source": "excel", "type": "monthly_comparison", "id": null, "title": "Monthly Revenue"}
        ]
    }
}
```

### Interactive Features

The monthly comparison chart includes:

- **Grouped bar chart** - Compare same months across different years side by side (e.g., January 2024 vs January 2025)
- **Dropdown selector** - Switch between "All Months" view or individual months (January-December)
- **Arrow key navigation** - Press ← → to cycle through months (All → Jan → Feb → ... → Dec → All)

## Example Use Cases

### Financial Tracking

Track yearly savings, investments, or expenses:

```json
{
    "name": "Yearly Savings",
    "file_path": "D:/Finance/savings.xlsx",
    "tabs": {
        "2020": "D2:D",
        "2021": "D2:D",
        "2022": "D2:D",
        "2023": "D2:D",
        "2024": "D2:D",
        "2025": "D2:D"
    },
    "unit_label": "EUR"
}
```

### Health Metrics

Track annual totals like exercise distance or weight changes:

```json
{
    "name": "Annual Running",
    "file_path": "D:/Health/running.xlsx",
    "tabs": {
        "2023": "C2:C",
        "2024": "C2:C",
        "2025": "C2:C"
    },
    "unit_label": "km"
}
```

## Troubleshooting

### File Not Found

Ensure the `file_path` uses forward slashes or escaped backslashes:
- Correct: `"C:/path/to/file.xlsx"` or `"C:\\path\\to\\file.xlsx"`
- Incorrect: `"C:\path\to\file.xlsx"`

### Tab Not Found

If a tab name doesn't exist in the Excel file, it returns 0 for that year. Check that tab names in your config match exactly (case-sensitive).

### Empty Results

- Verify the column range points to cells with numeric values
- Check that values are numbers, not formatted as text
- Ensure the start row doesn't skip your data
