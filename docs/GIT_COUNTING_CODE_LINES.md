# Git Stats: How Line Counting Works

This document explains how the Git Stats feature counts lines of code and how to verify the results manually.

## How It Works

### 1. Git Log with Numstat

The app uses `git log --numstat` to get line-by-line statistics for each commit:

```bash
git log --author="Your Name" --pretty=tformat:---COMMIT--- --numstat
```

Output format:
```
---COMMIT---
added<tab>removed<tab>filepath
added<tab>removed<tab>filepath
---COMMIT---
...
```

### 2. Date Range Filtering

For bounded queries (e.g., "Last 7 days"), git filters by commit date:

```bash
git log --since="2025-12-27 00:00:00" --until="2026-01-02 23:59:59" ...
```

- `--since` includes the start of the day (00:00:00)
- `--until` includes the end of the day (23:59:59)

### 3. Exclusion Filters

The app excludes files that aren't meaningful code:

| Category | Examples | Reason |
|----------|----------|--------|
| **Directories** | `node_modules`, `vendor`, `venv`, `build`, `dist` | Dependencies & build output |
| **Extensions** | `.json`, `.md`, `.yaml`, `.css`, `.png` | Config, docs, assets |
| **Filenames** | `package-lock.json`, `yarn.lock` | Lock files |

See `src/quantify/config/settings.py` for the full list.

### 4. SQLite Caching

Daily stats are cached to avoid repeated git queries:

- **Cache location**: `~/.quantify-your-life/git_stats_cache.db`
- **Schema**: `(repo_path, date, added, removed, commits)`
- **Today is never cached** (commits may still be added)
- **Exclusion rules are applied before caching**

## Real-World Example: Why High Numbers Can Be Correct

### The Scenario

User sees "Top 10 Repos (Last 7 days)" showing **+5,807 net lines** for a project. This seems too high for just 7 days.

### Investigation

Checking the cache:
```bash
sqlite3 ~/.quantify-your-life/git_stats_cache.db \
  "SELECT date, added, removed, commits FROM daily_stats
   WHERE repo_path LIKE '%project-name%' ORDER BY date DESC LIMIT 7"
```

Result:
```
2026-01-01|5569|617|9
2026-01-02|238|0|2
```

Checking git commit dates:
```bash
git log --since="2026-01-01" --until="2026-01-01 23:59:59" --format="%ai | %s"
```

Result:
```
2026-01-01 15:13:46 +0100 | FEATURE: add main feature
2026-01-01 14:11:39 +0100 | CONTENT: add docs
...
2026-01-01 12:39:54 +0100 | INITIAL COMMIT
```

### Root Cause

The project was **created on January 1st, 2026**. When querying "Last 7 days" (Dec 27 - Jan 2), the creation date falls within that window.

**All initial code counts as "added lines"** because that's when it was first committed to git. This is correct git behavior - not a bug.

### Key Insight

> If a project's creation date falls within your query period, you'll see the entire codebase counted as "added lines."

## Manual Verification Steps

### Step 1: Query the Cache

```bash
# View cached data for a specific repo
sqlite3 ~/.quantify-your-life/git_stats_cache.db \
  "SELECT repo_path, date, added, removed, commits
   FROM daily_stats
   WHERE repo_path LIKE '%your-repo%'
   ORDER BY date DESC
   LIMIT 20"
```

### Step 2: Verify with Git (Same Date Range)

```bash
# Get raw numstat for a date range
git -C "/path/to/repo" log \
  --since="2025-12-27 00:00:00" \
  --until="2026-01-02 23:59:59" \
  --author="Your Name" \
  --pretty=tformat:---COMMIT--- \
  --numstat
```

### Step 3: Count Lines Manually

```bash
# Sum all added/removed lines (no exclusions)
git -C "/path/to/repo" log \
  --since="2025-12-27" --until="2026-01-02" \
  --author="Your Name" \
  --pretty=tformat: --numstat | \
  awk 'NF==3 && $1 ~ /^[0-9]+$/ {a+=$1; d+=$2} END {print "added:",a,"removed:",d,"net:",a-d}'
```

### Step 4: Check Commit Dates

```bash
# See actual commit timestamps
git log --since="2026-01-01" --until="2026-01-01 23:59:59" \
  --author="Your Name" \
  --format="%ai | %s"
```

### Step 5: Compare Numbers

| Source | Added | Removed | Net | Notes |
|--------|-------|---------|-----|-------|
| App | 5,807 | X | 5,807 | After exclusions |
| Manual git | 6,939 | X | 6,939 | No exclusions |

The difference (~1,100 lines) should be from excluded files (.md, .json, .yaml, etc.).

## Troubleshooting

### Numbers seem too high?

1. Check if the project was recently created
2. Check if the query period includes the initial commit
3. Use "Debug Git Exclusions" menu to see what's being excluded

### Numbers don't match manual check?

1. Ensure you're using the same date range
2. Ensure you're using the same author filter
3. Remember the app applies many exclusions - manual queries usually don't

### Clear the cache to start fresh

Use the app: Git Stats → Database → Clear cache for a repository

Or manually:
```bash
sqlite3 ~/.quantify-your-life/git_stats_cache.db \
  "DELETE FROM daily_stats WHERE repo_path LIKE '%your-repo%'"
```

## Summary

- Line counts come from `git log --numstat`
- Many file types are excluded (config, docs, assets)
- Results are cached daily for performance
- Initial commits count as "added lines" - this is correct
- Use the manual verification steps to understand any discrepancies
