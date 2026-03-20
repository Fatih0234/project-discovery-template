from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from .config import lib_data_dir
from .github_api import search_repos
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
    items = search_repos(library, language=language, limit=limit)
    candidates = [_parse_candidate(item) for item in items]

    cache_path.write_text(
        json.dumps([c.model_dump(mode="json") for c in candidates], indent=2)
    )
    console.print(f"[green]Found {len(candidates)} candidates → {cache_path}[/green]")
    return candidates
