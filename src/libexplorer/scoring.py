from __future__ import annotations

import json
import math
from datetime import datetime, timezone

from rich.console import Console

from .config import lib_data_dir
from .models import ScoredRepo, VerifiedRepo

console = Console()

WEIGHTS = {
    "evidence": 0.35,
    "learnability": 0.20,
    "quality": 0.15,
    "recency": 0.10,
    "popularity": 0.10,
    "readme": 0.10,
}


def _evidence_score(v: VerifiedRepo) -> float:
    total = v.total_evidence
    if total == 0:
        return 0.0
    return min(1.0, total / 50.0)


def _learnability_score(v: VerifiedRepo) -> float:
    """More files matched → code is spread out → easier to study."""
    n = len(v.matched_files)
    if n == 0:
        return 0.0
    return min(1.0, n / 15.0)


def _quality_score(v: VerifiedRepo) -> float:
    c = v.candidate
    score = 0.0
    if c.license and c.license not in ("NOASSERTION", "OTHER"):
        score += 0.4
    if c.topics:
        score += min(0.3, len(c.topics) * 0.1)
    if c.open_issues_count > 0:
        score += 0.3
    return min(1.0, score)


def _recency_score(v: VerifiedRepo) -> float:
    if not v.candidate.pushed_at:
        return 0.0
    now = datetime.now(timezone.utc)
    days_ago = (now - v.candidate.pushed_at).days
    if days_ago <= 30:
        return 1.0
    if days_ago <= 180:
        return 0.7
    if days_ago <= 365:
        return 0.4
    if days_ago <= 730:
        return 0.2
    return 0.0


def _popularity_score(v: VerifiedRepo) -> float:
    stars = v.candidate.stargazers_count
    return min(1.0, math.log1p(stars) / math.log1p(5000))


def _readme_score(v: VerifiedRepo) -> float:
    # Only award README score if the repo also has real code imports.
    # A README-only mention (no imports) is not reliable usage evidence.
    if v.import_count == 0:
        return 0.0
    return 1.0 if v.readme_snippet else 0.0


def score_repo(v: VerifiedRepo) -> ScoredRepo:
    breakdown = {
        "evidence": _evidence_score(v),
        "learnability": _learnability_score(v),
        "quality": _quality_score(v),
        "recency": _recency_score(v),
        "popularity": _popularity_score(v),
        "readme": _readme_score(v),
    }
    total = sum(WEIGHTS[k] * breakdown[k] for k in WEIGHTS)
    return ScoredRepo(verified=v, score=round(total, 4), score_breakdown=breakdown)


def score(
    library: str,
    verified: list[VerifiedRepo],
    skip_cache: bool = False,
) -> list[ScoredRepo]:
    data_dir = lib_data_dir(library)
    cache_path = data_dir / "ranked.json"

    if cache_path.exists() and not skip_cache:
        console.print(f"[dim]Loading ranked from cache: {cache_path}[/dim]")
        raw = json.loads(cache_path.read_text())
        return [ScoredRepo.model_validate(r) for r in raw]

    # Hard evidence gate: repos with zero code imports are rejected before scoring.
    accepted = [v for v in verified if v.import_count >= 1]
    rejected = [v for v in verified if v.import_count == 0]

    if rejected:
        rejected_path = data_dir / "rejected_candidates.json"
        rejected_path.write_text(
            json.dumps(
                [
                    {
                        "full_name": v.candidate.full_name,
                        "stars": v.candidate.stargazers_count,
                        "import_count": v.import_count,
                        "rejection_reason": "no_code_evidence",
                    }
                    for v in rejected
                ],
                indent=2,
            )
        )
        console.print(
            f"[yellow]Rejected {len(rejected)} repos with no code evidence "
            f"→ {rejected_path}[/yellow]"
        )

    scored = sorted([score_repo(v) for v in accepted], key=lambda s: s.score, reverse=True)

    cache_path.write_text(
        json.dumps([s.model_dump(mode="json") for s in scored], indent=2)
    )
    console.print(f"[green]Scored & ranked {len(scored)} repos → {cache_path}[/green]")
    return scored
