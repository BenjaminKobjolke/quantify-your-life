# Projects Created

Counts the number of repositories where the configured author made their first commit within the selected time period.

## Git Command

```bash
git -C <repo_path> log --author=<author> --reverse --format=%ad --date=short -1
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `repo_path` | Absolute path to the git repository |
| `author` | Git author name from config (e.g., "John Doe") |

### Example

```bash
git -C "D:/GIT/my-project" log --author="Benjamin Kobjolke" --reverse --format=%ad --date=short -1
```

## Output Format

```
2025-03-15
```

Returns the date of the first commit by the author in ISO format (YYYY-MM-DD).

## Processing

1. For each repository, get the date of the first commit by the author
2. Check if that date falls within the selected time period
3. Count repositories where the first commit is in range

## Algorithm

```python
for repo in all_repositories:
    first_commit_date = get_first_commit_date(repo)
    if first_commit_date is not None:
        if start_date <= first_commit_date <= end_date:
            count += 1
```

## Details View

When viewing projects created, you can show a detailed list:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Projects Created (Last year (2025))        ┃
┣━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┫
┃  # ┃ Repository            ┃       Created ┃
┣━━━━╋━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━┫
┃  1 ┃ new-project-alpha     ┃    2025-02-14 ┃
┃  2 ┃ cool-library          ┃    2025-05-22 ┃
┗━━━━┻━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━┛
```

## Notes

- A "project created" means the author's **first commit** in that repository
- This could be creating a new repository OR joining an existing one
- Repositories with no commits by the author are not counted

## Code Reference

- Command built in: `src/quantify/sources/git_stats/git_log_parser.py:284-294`
- First commit date logic: `src/quantify/sources/git_stats/git_log_parser.py:270-305`
- Projects in period: `src/quantify/sources/git_stats/source.py:296-347`
