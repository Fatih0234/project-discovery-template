# Copilot instructions for library-usecase-explorer

This repository builds a developer research workspace that discovers real-world GitHub repositories using a target library/framework, verifies actual usage in code, ranks the best examples for junior developers, and generates beginner-friendly markdown reports.

## Product intent
- The audience is junior developers learning libraries and frameworks.
- Prefer clarity, determinism, and inspectability over cleverness.
- Use LLMs for summarization over collected evidence, not as the primary discovery mechanism.
- Optimize outputs for "what can I learn from this repo?" rather than generic repo search.

## Engineering principles
- Keep the GitHub API layer isolated.
- Prefer small pure functions and explicit data models.
- Make scoring transparent and easy to modify.
- Preserve intermediate artifacts in `data/`.
- Write readable markdown reports in `reports/`.
- Fail gracefully when tokens or quotas are unavailable.

## Coding conventions
- Use Python type hints and docstrings.
- Keep modules cohesive.
- Avoid hidden global state.
- Prefer deterministic heuristics in V1.
- Add tests for ranking, verification heuristics, and reporting.

## Workspace conventions
- Source code lives in `src/libexplorer/`.
- Jinja templates live in `templates/`.
- Cached artifacts live in `data/<library>/`.
- Final outputs live in `reports/<library>/`.

## When changing behavior
- Update README if commands or architecture change.
- Update tests when scoring or output formats change.
- Keep the CLI user experience simple.