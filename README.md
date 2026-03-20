# library-usecase-explorer

Discover real-world GitHub repositories that use any Python library, score them by educational value, and generate a structured markdown report — all from one CLI command.

## Quick Start

```bash
# 1. Copy env file and fill in keys
cp .env.example .env

# 2. Install
pip install -e .[dev]

# 3. Run example (tenacity)
libexplorer analyze tenacity --language python --top-k 5

# 4. Read your report
cat reports/tenacity/final_report.md
```

Or with Make:

```bash
make install
make example
```

---

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GITHUB_TOKEN` | Recommended | GitHub search API + GitHub Models for AI summaries |
| `GH_TOKEN` | — | Same as above — use this name in Codespaces secrets (GitHub blocks the `GITHUB_` prefix) |

One token does everything. If no token is set, GitHub rate-limits you to 10 req/min and summaries fall back to a template.

---

## Commands

```bash
# Full pipeline
libexplorer analyze <library> [--language python] [--top-k 5] [--limit 50] [--skip-cache]

# Discovery only (GitHub search)
libexplorer discover <library>

# Re-render report from cached data (no network)
libexplorer report <library>

# Version
libexplorer --version
```

---

## Architecture

```
src/libexplorer/
├── cli.py           # Typer CLI entrypoint
├── config.py        # Env vars + paths
├── models.py        # Pydantic data models
├── github_api.py    # GitHub REST API calls
├── discovery.py     # Step 1: search repos
├── verification.py  # Step 2: detect evidence (imports, decorators, calls)
├── scoring.py       # Step 3: weighted score
├── extraction.py    # Step 4: build RepoDigest objects
├── summarization.py # Step 5: LLM or template synthesis
└── reporting.py     # Step 6: Jinja2 → final_report.md
```

### Pipeline

```
GitHub Search
    │
    ▼
candidates.json       (CandidateRepo list)
    │
    ▼  code search + regex evidence detection
verified.json         (VerifiedRepo list)
    │
    ▼  weighted scoring
ranked.json           (ScoredRepo list, sorted)
    │
    ▼  top-k extraction
top_repos/<slug>.json (RepoDigest per repo)
    │
    ▼  LLM or template
synthesis string
    │
    ▼  Jinja2 render
reports/<lib>/final_report.md
```

### Scoring Weights

| Dimension | Weight | Signal |
|-----------|--------|--------|
| Evidence | 35% | Import/decorator/call count |
| Learnability | 20% | Number of distinct files using the lib |
| Quality | 15% | License + topics + issue activity |
| Recency | 10% | Days since last push |
| Popularity | 10% | Log-scaled stars |
| README | 10% | Library mentioned in README |

---

## Tenacity Example

```bash
libexplorer analyze tenacity --language python --top-k 5
```

Expected output: `reports/tenacity/final_report.md` with:
- Top 5 repos using `tenacity` for retry logic
- Evidence counts (imports, `@retry` decorators, `tenacity.stop_*` calls)
- Synthesis covering HTTP retry, background job resilience, and async patterns

---

## Extending the Scorer

Edit `src/libexplorer/scoring.py`. Each sub-scorer is an isolated function `_X_score(v: VerifiedRepo) → float` returning 0–1. Add a new one and register it in `WEIGHTS` (keep weights summing to 1.0).

```python
def _test_coverage_score(v: VerifiedRepo) -> float:
    test_files = [f for f in v.matched_files if "test" in f]
    return min(1.0, len(test_files) / 3.0)

WEIGHTS = {
    ...
    "test_coverage": 0.05,  # reduce other weights to compensate
}
```

---

## Tests

```bash
pytest tests/ -v
```

Tests cover:
- `test_scoring.py` — weighted score math, edge cases
- `test_verification.py` — regex evidence detection
- `test_reporting.py` — Jinja2 template rendering

---

## Codespaces

Open in GitHub Codespaces — the container will auto-install dependencies and print available commands.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/your-org/library-usecase-explorer)
