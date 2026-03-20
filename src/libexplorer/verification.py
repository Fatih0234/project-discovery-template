from __future__ import annotations

import json
import re

from rich.console import Console
from rich.progress import track

from .config import lib_data_dir
from .github_api import get_file_content, get_readme, search_code
from .models import CandidateRepo, CodeSnippet, VerifiedRepo

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


def _extract_snippets(
    library: str,
    content: str,
    file_path: str,
    max_per_type: int = 3,
) -> list[CodeSnippet]:
    """Extract up to max_per_type code snippets (±5 lines) per match type."""
    lib = re.escape(library)
    patterns: list[tuple[re.Pattern, str]] = [
        (re.compile(r"^\s*import\s+" + lib + r"\b", re.MULTILINE), "import"),
        (re.compile(r"^\s*from\s+" + lib + r"\b.*import", re.MULTILINE), "import"),
        (re.compile(r"@" + lib + r"\.", re.MULTILINE), "decorator"),
        (re.compile(lib + r"\.\w+\s*\(", re.MULTILINE), "call"),
    ]

    lines = content.splitlines()
    snippets: list[CodeSnippet] = []
    seen_lines: set[int] = set()
    counts: dict[str, int] = {}

    for pattern, match_type in patterns:
        for m in pattern.finditer(content):
            if counts.get(match_type, 0) >= max_per_type:
                break
            line_no = content[: m.start()].count("\n")
            if line_no in seen_lines:
                continue
            seen_lines.add(line_no)
            start = max(0, line_no - 5)
            end = min(len(lines), line_no + 6)
            snippet_text = "\n".join(lines[start:end])[:500]
            snippets.append(
                CodeSnippet(
                    file_path=file_path,
                    line_no=line_no + 1,
                    snippet=snippet_text,
                    match_type=match_type,
                )
            )
            counts[match_type] = counts.get(match_type, 0) + 1

    return snippets


def _is_self_repo(library: str, full_name: str) -> bool:
    """Return True if this repo appears to be the library's own repository."""
    repo_name = full_name.split("/")[-1].lower()
    lib_lower = library.lower().replace("-", "").replace("_", "")
    repo_normalized = repo_name.replace("-", "").replace("_", "")
    return repo_normalized == lib_lower


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

    # Exclude the library's own repo before verification
    filtered = [c for c in candidates if not _is_self_repo(library, c.full_name)]
    excluded = len(candidates) - len(filtered)
    if excluded:
        console.print(f"[yellow]Excluded {excluded} self-repo candidate(s)[/yellow]")

    verified: list[VerifiedRepo] = []

    for candidate in track(filtered, description="Verifying repos..."):
        code_items = search_code(library, candidate.full_name)
        matched_files: list[str] = []
        all_snippets: list[CodeSnippet] = []
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
                all_snippets.extend(_extract_snippets(library, content, path))

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
                code_snippets=all_snippets[:15],  # cap total snippets per repo
            )
        )

    cache_path.write_text(
        json.dumps([v.model_dump(mode="json") for v in verified], indent=2)
    )
    console.print(f"[green]Verified {len(verified)} repos → {cache_path}[/green]")
    return verified
