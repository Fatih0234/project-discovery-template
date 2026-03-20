from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from .config import lib_data_dir
from .github_api import search_repos, search_repos_by_code, search_repos_by_topic
from .models import CandidateRepo

console = Console()


def _parse_candidate(item: dict) -> CandidateRepo:
    pushed = item.get("pushed_at")
    return CandidateRepo(
        full_name=item["full_name"],
        html_url=item["html_url"],
        description=item.get("description"),
        stargazers_count=item.get("stargazers_count", 0),
        forks_count=item.get("forks_count", 0),
        open_issues_count=item.get("open_issues_count", 0),
        pushed_at=datetime.fromisoformat(pushed.replace("Z", "+00:00")) if pushed else None,
        language=item.get("language"),
        topics=item.get("topics", []),
        license=item.get("license", {}).get("spdx_id") if item.get("license") else None,
    )


def _is_self_repo(library: str, full_name: str) -> bool:
    """Return True if the repo appears to be the library's own repository."""
    repo_name = full_name.split("/")[-1].lower()
    lib_lower = library.lower().replace("-", "").replace("_", "")
    repo_normalized = repo_name.replace("-", "").replace("_", "")
    return repo_normalized == lib_lower


def discover(
    library: str,
    language: str = "python",
    limit: int = 50,
    skip_cache: bool = False,
) -> list[CandidateRepo]:
    data_dir = lib_data_dir(library)
    cache_path = data_dir / "candidates.json"

    if cache_path.exists() and not skip_cache:
        console.print(f"[dim]Loading candidates from cache: {cache_path}[/dim]")
        raw = json.loads(cache_path.read_text())
        return [CandidateRepo.model_validate(r) for r in raw]

    console.print(f"[bold]Searching GitHub for repos using [cyan]{library}[/cyan]...[/bold]")

    # Three complementary search strategies — union and deduplicate
    name_items = search_repos(library, language=language, limit=limit)
    console.print(f"  [dim]Name search: {len(name_items)} results[/dim]")

    topic_items = search_repos_by_topic(library, language=language, limit=limit // 2)
    console.print(f"  [dim]Topic search: {len(topic_items)} results[/dim]")

    code_items = search_repos_by_code(library, language=language, limit=limit // 2)
    console.print(f"  [dim]Code search: {len(code_items)} results[/dim]")

    # Merge, deduplicate by full_name, exclude the library's own repo
    seen: set[str] = set()
    merged: list[dict] = []
    for item in name_items + topic_items + code_items:
        full_name = item.get("full_name", "")
        if not full_name or full_name in seen:
            continue
        if _is_self_repo(library, full_name):
            console.print(f"  [dim]Skipping self-repo: {full_name}[/dim]")
            continue
        seen.add(full_name)
        merged.append(item)

    # Sort by stars descending and cap at limit
    merged.sort(key=lambda x: x.get("stargazers_count", 0), reverse=True)
    candidates = [_parse_candidate(item) for item in merged[:limit]]

    cache_path.write_text(
        json.dumps([c.model_dump(mode="json") for c in candidates], indent=2)
    )
    console.print(f"[green]Found {len(candidates)} candidates → {cache_path}[/green]")
    return candidates
