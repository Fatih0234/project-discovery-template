from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from .config import lib_data_dir
from .models import RepoCategory, RepoDigest, ScoredRepo

console = Console()

_USE_CASE_KEYWORDS: dict[str, list[str]] = {
    "retry": ["retry", "retrying", "backoff", "attempt"],
    "async": ["async", "asyncio", "await"],
    "cli": ["cli", "command", "argparse", "typer", "click"],
    "web": ["fastapi", "flask", "django", "aiohttp", "starlette"],
    "data": ["pandas", "numpy", "dataset", "etl"],
    "testing": ["pytest", "unittest", "test"],
    "ml": ["torch", "tensorflow", "sklearn", "model", "train"],
}

_TUTORIAL_KEYWORDS = {"tutorial", "example", "demo", "sample", "learn", "course", "workshop"}
_WRAPPER_KEYWORDS = {"wrapper", "extension", "plugin", "adapter", "middleware", "integration"}


def _infer_use_case_tags(repo: ScoredRepo) -> list[str]:
    text = " ".join([
        repo.verified.candidate.description or "",
        " ".join(repo.verified.candidate.topics),
        " ".join(repo.verified.matched_files),
        repo.verified.readme_snippet or "",
    ]).lower()
    return [tag for tag, keywords in _USE_CASE_KEYWORDS.items() if any(kw in text for kw in keywords)]


def _classify_repo(repo: ScoredRepo, library: str) -> RepoCategory:
    """Classify a repo into a category based on heuristics."""
    description = (repo.verified.candidate.description or "").lower()
    topics = {t.lower() for t in repo.verified.candidate.topics}
    files = " ".join(repo.verified.matched_files).lower()

    # Tutorial / example repos
    if any(kw in description for kw in _TUTORIAL_KEYWORDS) or (topics & _TUTORIAL_KEYWORDS):
        return RepoCategory.TUTORIAL

    # Wrapper / extension repos
    if any(kw in description for kw in _WRAPPER_KEYWORDS) or (topics & _WRAPPER_KEYWORDS):
        return RepoCategory.WRAPPER

    # If all matched files are in test directories, treat as testing-only (low learning value)
    if repo.verified.matched_files and all(
        "test" in f or "spec" in f for f in repo.verified.matched_files
    ):
        return RepoCategory.TUTORIAL  # treat test-only as limited-scope example

    return RepoCategory.APP


def extract_digests(
    library: str,
    ranked: list[ScoredRepo],
    top_k: int = 5,
    skip_cache: bool = False,
) -> list[RepoDigest]:
    data_dir = lib_data_dir(library)
    top_dir = data_dir / "top_repos"
    top_dir.mkdir(exist_ok=True)

    digests: list[RepoDigest] = []
    for repo in ranked[:top_k]:
        slug = repo.verified.candidate.full_name.replace("/", "__")
        cache_path = top_dir / f"{slug}.json"

        if cache_path.exists() and not skip_cache:
            digests.append(RepoDigest.model_validate(json.loads(cache_path.read_text())))
            continue

        digest = RepoDigest(
            full_name=repo.verified.candidate.full_name,
            html_url=repo.verified.candidate.html_url,
            description=repo.verified.candidate.description,
            stars=repo.verified.candidate.stargazers_count,
            language=repo.verified.candidate.language,
            topics=repo.verified.candidate.topics,
            license=repo.verified.candidate.license,
            score=repo.score,
            evidence_summary={
                "imports": repo.verified.import_count,
                "decorators": repo.verified.decorator_count,
                "function_calls": repo.verified.function_call_count,
            },
            readme_snippet=repo.verified.readme_snippet,
            matched_files=repo.verified.matched_files,
            use_case_tags=_infer_use_case_tags(repo),
            code_snippets=repo.verified.code_snippets,
            repo_category=_classify_repo(repo, library),
        )
        cache_path.write_text(json.dumps(digest.model_dump(mode="json"), indent=2))
        digests.append(digest)

    console.print(f"[green]Extracted {len(digests)} digests → {top_dir}[/green]")
    return digests
