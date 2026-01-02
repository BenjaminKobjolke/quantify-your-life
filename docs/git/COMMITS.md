# Commits

Counts the total number of commits made by the configured author across all repositories.

## Git Command

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

## Output Format

```
---COMMIT---
15      3       src/main.py
42      10      src/utils.py
---COMMIT---
8       2       README.md
```

- `---COMMIT---` marks each commit boundary
- Each file line: `<added>\t<removed>\t<filepath>`

## Processing

1. Count occurrences of `---COMMIT---` marker in output
2. Each marker represents one commit by the author
3. Sum across all repositories

## Details View

When viewing commits, you can show a detailed breakdown by repository:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Commits by Repository (Last year (2025))  ┃
┣━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┫
┃  # ┃ Repository            ┃       Commits ┃
┣━━━━╋━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━┫
┃  1 ┃ quantify-your-life    ┃           523 ┃
┃  2 ┃ my-other-project      ┃           312 ┃
┗━━━━┻━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━┛
```

## Code Reference

- Command built in: `src/quantify/sources/git_stats/git_log_parser.py:121-136`
- Commit counting: `src/quantify/sources/git_stats/git_log_parser.py:170-173`
- Details view: `src/quantify/sources/git_stats/source.py:349-407`
