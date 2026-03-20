from __future__ import annotations

import json
import re

from rich.console import Console
from rich.progress import track

from .config import lib_data_dir
from .github_api import get_file_content, get_readme, search_code
from .models import CandidateRepo, VerifiedRepo

console = Console()

_IMPORT_PATTERNS = [
    re.compile(r"^\s*import\s+{lib}\b", re.MULTILINE),
    re.compile(r"^\s*from\s+{lib}\b.*import", re.MULTILINE),
]
_DECORATOR_PATTERN = re.compile(r"@{lib}\.", )
_CALL_PATTERN = re.compile(r"{lib}\.\w+\s*\(")


def _count_evidence(library: str, content: str) -> tuple[int, int, int]:
    lib = re.escape(library)
    imports = sum(
        len(re.findall(p.pattern.replace("{lib}", lib), content, re.MULTILINE))
        for p in _IMPORT_PATTERNS
    )
    decorators = len(re.findall(_DECORATOR_PATTERN.pattern.replace("{lib}", lib), content))
    calls = len(re.findall(_CALL_PATTERN.pattern.replace("{lib}", lib), content))
    return imports, decorators, calls


def verify(
    library: str,
    candidates: list[CandidateRepo],
    skip_cache: bool = False,
) -> list[VerifiedRepo]:
    data_dir = lib_data_dir(library)
    cache_path = data_dir / "verified.json"

    if cache_path.exists() and not skip_cache:
        console.print(f"[dim]Loading verified from cache: {cache_path}[/dim]")
        raw = json.loads(cache_path.read_text())
        return [VerifiedRepo.model_validate(r) for r in raw]

    verified: list[VerifiedRepo] = []

    for candidate in track(candidates, description="Verifying repos..."):
        code_items = search_code(library, candidate.full_name)
        matched_files: list[str] = []
        total_imports = total_decorators = total_calls = 0

        for item in code_items[:10]:
            path = item.get("path", "")
            content = get_file_content(candidate.full_name, path) or ""
            imp, dec, cal = _count_evidence(library, content)
            if imp + dec + cal > 0:
                matched_files.append(path)
                total_imports += imp
                total_decorators += dec
                total_calls += cal

        readme = get_readme(candidate.full_name)
        readme_snippet: str | None = None
        if readme:
            imp, dec, cal = _count_evidence(library, readme)
            total_imports += imp
            total_decorators += dec
            total_calls += cal
            # Grab first paragraph mentioning the library
            for line in readme.splitlines():
                if library.lower() in line.lower() and len(line.strip()) > 20:
                    readme_snippet = line.strip()[:400]
                    break

        verified.append(
            VerifiedRepo(
                candidate=candidate,
                import_count=total_imports,
                decorator_count=total_decorators,
                function_call_count=total_calls,
                matched_files=matched_files,
                readme_snippet=readme_snippet,
            )
        )

    cache_path.write_text(
        json.dumps([v.model_dump(mode="json") for v in verified], indent=2)
    )
    console.print(f"[green]Verified {len(verified)} repos → {cache_path}[/green]")
    return verified
