# Net Lines

Calculates the net change in lines of code (added - removed) by the configured author across all repositories.

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
- Binary files show `-` for added/removed

## Processing

1. Parse each line after `---COMMIT---`
2. Extract both columns (added and removed lines)
3. Sum all values across all commits
4. Calculate net: `total_added - total_removed`
5. Apply exclusion filters (directories, extensions, filenames)

## Calculation

```python
net_lines = total_added - total_removed
```

- **Positive value**: More code added than removed (codebase grew)
- **Negative value**: More code removed than added (codebase shrank)
- **Zero**: Equal amounts added and removed

## Exclusion Filters

Files are excluded if they match:
- **Directories**: `node_modules`, `.git`, `vendor`, etc.
- **Extensions**: `.min.js`, `.lock`, etc.
- **Filenames**: `package-lock.json`, etc.
- **Include patterns**: For project types like Unity, only specific patterns are counted

## Code Reference

- Command built in: `src/quantify/sources/git_stats/git_log_parser.py:121-136`
- Parsing logic: `src/quantify/sources/git_stats/git_log_parser.py:150-196`
- Net calculation: `src/quantify/sources/git_stats/git_log_parser.py:24-27`
