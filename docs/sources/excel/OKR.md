# OKR (Objectives & Key Results) Excel Source

Track Key Results progress over time from Excel files with automatic prognosis projection.

## Config

In `config.json`, add an Excel source with `source_type: "OKR"` and `tabs` as a list:

```json
{
  "source_type": "OKR",
  "name": "Q1 OKRs",
  "file": "data/okr.xlsx",
  "tabs": ["OKR Q1 2026"]
}
```

## Excel Tab Structure

Each OKR tab must follow this row layout:

| Row | Content | Example |
|-----|---------|---------|
| 1 | Headers: KW, Datum, then KR name + % pairs | `KW`, `Datum`, `KR1 Klicks/w`, `KR1 %`, `KR2 Umsatz`, `KR2 %` |
| 2 | Ziele (targets) in value columns | `""`, `""`, `500`, `""`, `10000`, `""` |
| 3 | Zieldatum (target date) in column B or C | `""`, `31.03.2026` |
| 4 | Startwert (start values) | `""`, `""`, `0`, `0%`, `0`, `0%` |
| 5+ | Weekly data rows | `1`, `06.01.2026`, `12`, `2%`, `150`, `1.5%` |

- **Column A**: Calendar week number (KW)
- **Column B**: Date (DD.MM.YYYY format or Excel date)
- **Columns C+**: Alternating KR value / KR percentage pairs
- KR columns are auto-detected from row 1 headers

## Prognosis Line

When a Zieldatum (target date) is present in row 3, the chart displays a **dashed prognosis line** for each KR:

- Projects from the last actual data point forward to the target date
- Uses average weekly progress rate: `last_percentage / number_of_data_points`
- Generates weekly future dates until the target date
- Capped at 100%
- Displayed as a dashed line in the same color as the actual KR line
- Hidden from the chart legend

## Export Entry

Add to the project's `exports` array:

```json
{
  "type": "okr",
  "source": "Q1 OKRs",
  "tab": "OKR Q1 2026",
  "title": "OKR Progress Q1",
  "filename": "okr_q1.html"
}
```
