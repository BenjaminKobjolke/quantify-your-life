# Multi-Threading for Git Tasks

## Overview
Add multi-threading to parallelize git operations across repositories. Git subprocess calls are I/O bound, making them ideal candidates for `ThreadPoolExecutor`.

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/quantify/sources/git_stats/git_log_parser.py` | Add thread lock for `_failed_repos` set |
| `src/quantify/sources/git_stats/data_provider.py` | Parallelize repo iteration in `get_sum()` and `ProjectsCreatedDataProvider` |
| `src/quantify/sources/git_stats/source.py` | Parallelize `get_top_repos()` |

---

## Feature 1: Thread-Safe GitLogParser

### Problem
`_failed_repos` set is modified during parsing - not thread-safe.

### Implementation
Add a threading lock to protect shared state:

```python
import threading

class GitLogParser:
    def __init__(self, ...):
        ...
        self._failed_repos: set[Path] = set()
        self._lock = threading.Lock()

    def get_stats(self, repo_path, ...):
        with self._lock:
            if repo_path in self._failed_repos:
                return GitStats(added=0, removed=0, commits=0)

        try:
            # ... existing logic ...
        except ...:
            with self._lock:
                self._failed_repos.add(repo_path)
            return GitStats(...)
```

---

## Feature 2: Parallel GitStatsDataProvider.get_sum()

### Current Flow (Sequential)
```python
for idx, repo in enumerate(self._repos):
    added, removed, commits = self._get_repo_stats_cached(repo, start_date, end_date)
    total_added += added
    ...
```

### New Flow (Parallel)
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_sum(self, start_date, end_date) -> float:
    if start_date is None:
        return self._get_sum_uncached(start_date, end_date)

    effective_end = end_date if end_date is not None else date.today()
    total_added = 0
    total_removed = 0
    total_commits = 0
    total_repos = len(self._repos)
    completed = 0

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(self._get_repo_stats_cached, repo, start_date, effective_end): repo
            for repo in self._repos
        }

        for future in as_completed(futures):
            repo = futures[future]
            completed += 1
            if self._progress_callback:
                self._progress_callback(repo.name, completed, total_repos)

            added, removed, commits = future.result()
            total_added += added
            total_removed += removed
            total_commits += commits

    return float(self._compute_stat(total_added, total_removed, total_commits))
```

---

## Feature 3: Parallel _get_sum_uncached()

### Implementation
```python
def _get_sum_uncached(self, start_date, end_date) -> float:
    total = 0
    total_repos = len(self._repos)
    completed = 0

    def process_repo(repo: Path) -> int:
        stats = self._parser.get_stats(repo, start_date, end_date)
        return self._compute_stat(stats.added, stats.removed, stats.commits)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_repo, repo): repo for repo in self._repos}

        for future in as_completed(futures):
            repo = futures[future]
            completed += 1
            if self._progress_callback:
                self._progress_callback(repo.name, completed, total_repos)
            total += future.result()

    return float(total)
```

---

## Feature 4: Parallel ProjectsCreatedDataProvider.get_sum()

### Implementation
```python
def get_sum(self, start_date, end_date) -> float:
    effective_end = end_date if end_date is not None else date.today()
    count = 0
    total_repos = len(self._repos)
    completed = 0

    def check_repo(repo: Path) -> int:
        first_commit = self._get_first_commit_date(repo)
        if first_commit is None:
            return 0
        if start_date is not None and first_commit < start_date:
            return 0
        if first_commit > effective_end:
            return 0
        return 1

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(check_repo, repo): repo for repo in self._repos}

        for future in as_completed(futures):
            repo = futures[future]
            completed += 1
            if self._progress_callback:
                self._progress_callback(repo.name, completed, total_repos)
            count += future.result()

    return float(count)
```

---

## Feature 5: Parallel get_top_repos()

### Implementation
```python
def get_top_repos(self, start_date, end_date, limit=10) -> list[tuple[Path, int]]:
    self._ensure_initialized()
    assert self._repos is not None
    assert self._parser is not None
    assert self._cache is not None

    effective_end = end_date if end_date is not None else date.today()

    def get_repo_net(repo: Path) -> tuple[Path, int]:
        if start_date is None:
            stats = self._parser.get_stats(repo, start_date, effective_end)
            return (repo, stats.net)
        else:
            provider = GitStatsDataProvider(
                [repo], self._parser, self.STAT_NET, self._cache
            )
            return (repo, int(provider.get_sum(start_date, effective_end)))

    repo_stats: list[tuple[Path, int]] = []
    total_repos = len(self._repos)
    completed = 0

    with Progress(...) as progress:
        self._progress = progress
        self._task_id = progress.add_task("Analyzing repositories...", total=None)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(get_repo_net, repo): repo for repo in self._repos}

            for future in as_completed(futures):
                repo = futures[future]
                completed += 1
                self._on_progress(repo.name, completed, total_repos)
                repo_stats.append(future.result())

        self._progress = None
        self._task_id = None

    repo_stats.sort(key=lambda x: x[1], reverse=True)
    return repo_stats[:limit]
```

---

## Thread Safety Considerations

| Component | Status | Notes |
|-----------|--------|-------|
| `_failed_repos` set | Needs lock | Mutable shared state |
| SQLite cache | Thread-safe | Reads concurrent; writes serialized by SQLite |
| Progress callbacks | Safe | Order is non-sequential (as repos complete) |
| Git repository access | Safe | Concurrent reads allowed |
| `_first_commit_cache` dict | Needs lock | Or use per-thread instances |

---

## Configuration

- **Default workers**: 8 (balances CPU cores and I/O parallelism)
- **Future enhancement**: Make configurable via config.json

---

## Behavior Changes

### Progress Reporting
- **Before**: Progress fires sequentially (repo 1, repo 2, repo 3...)
- **After**: Progress fires as repos complete (order varies)
- The counter still shows `"Scanning {repo} ({completed}/{total})..."`

---

## Implementation Order

1. Add thread lock to `GitLogParser._failed_repos`
2. Update `GitStatsDataProvider.get_sum()` with ThreadPoolExecutor
3. Update `GitStatsDataProvider._get_sum_uncached()` with ThreadPoolExecutor
4. Update `ProjectsCreatedDataProvider.get_sum()` with ThreadPoolExecutor
5. Update `GitStatsSource.get_top_repos()` with ThreadPoolExecutor
6. Test with multiple repositories
