# Top 10 Repos

Shows the top 10 repositories ranked by net lines changed (added - removed) within the selected time period.

## Git Command

For each repository:

```bash
git -C <repo_path> log --author=<author> --pretty=tformat:---COMMIT--- --numstat --since=<start_date> 00:00:00 --until=<end_date> 23:59:59
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `repo_path` | Absolute path to the git repository |
| `author` | Git author name from config (e.g., "John Doe") |
| `start_date` | ISO format date (e.g., "2025-01-01") |
| `end_date` | ISO format date (e.g., "2025-12-31") |

### Example

```bash
git -C "D:/GIT/my-project" log --author="Benjamin Kobjolke" --pretty=tformat:---COMMIT--- --numstat --since="2025-01-01 00:00:00" --until="2025-12-31 23:59:59"
```

## Processing

1. For each repository in all configured root paths:
   - Run the git log command
   - Calculate net lines (added - removed)
2. Sort repositories by net lines descending
3. Return top 10

## Output Format

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Top 10 Repos (Last year (2025))           ┃
┣━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┫
┃  # ┃ Repository            ┃     Net Lines ┃
┣━━━━╋━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━┫
┃  1 ┃ quantify-your-life    ┃       +12,345 ┃
┃  2 ┃ web-application       ┃        +8,234 ┃
┃  3 ┃ api-backend           ┃        +5,123 ┃
┃  4 ┃ mobile-app            ┃        +3,456 ┃
┃  5 ┃ shared-library        ┃        +2,100 ┃
┃  6 ┃ documentation         ┃        +1,500 ┃
┃  7 ┃ testing-framework     ┃          +890 ┃
┃  8 ┃ config-tools          ┃          +456 ┃
┃  9 ┃ legacy-cleanup        ┃          -234 ┃
┃ 10 ┃ deprecated-module     ┃        -1,200 ┃
┗━━━━┻━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━┛
```

## Notes

- **Positive values** (+): More lines added than removed
- **Negative values** (-): More lines removed than added (refactoring/cleanup)
- Repositories with 0 net change are included in ranking
- Uses parallel processing (8 threads) for performance
- Results are cached for bounded date queries

## Performance

- Uses `ThreadPoolExecutor` with 8 workers for parallel queries
- Bounded queries use the SQLite cache for historical data
- Unbounded queries (all-time) query git directly

## Code Reference

- Main method: `src/quantify/sources/git_stats/source.py:232-294`
- Display: `src/quantify/cli/handlers/git_stats.py:120-136`
