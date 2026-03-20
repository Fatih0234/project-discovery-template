from __future__ import annotations

from .config import GITHUB_TOKEN, GITHUB_MODELS_API, GITHUB_MODELS_MODEL, llm_available
from .models import RepoDigest


def _template_summary(library: str, digests: list[RepoDigest]) -> str:
    top = digests[0] if digests else None
    repo_list = "\n".join(f"- [{d.full_name}]({d.html_url}) (score: {d.score:.2f})" for d in digests)
    use_cases = sorted({tag for d in digests for tag in d.use_case_tags})
    use_case_str = ", ".join(use_cases) if use_cases else "general usage"

    return f"""## Cross-Repo Synthesis

The top {len(digests)} repositories demonstrate **{library}** being used primarily for: {use_case_str}.

### Top Repositories
{repo_list}

### Common Patterns
- Most repos use `{library}` for its core functionality as the name suggests.
- Evidence was found across {sum(len(d.matched_files) for d in digests)} files in total.
- Typical usage involves importing the library and calling its main API.

### For Juniors
Start with **{top.full_name if top else 'any of the above'}** — it has readable code and clear documentation. Look at the files that import `{library}` directly.

### Common Mistakes to Avoid
- Not reading the official docs before copying patterns from GitHub.
- Using advanced features before understanding the basics.
- Ignoring error handling around library calls.

### Next Project Ideas
- Build a small CLI tool that uses `{library}` end-to-end.
- Add `{library}` to an existing project as a drop-in improvement.
- Write tests for code that uses `{library}` to understand its contract.
"""


def _format_digest_for_llm(d: RepoDigest) -> str:
    lines = [
        f"**{d.full_name}** (score={d.score:.2f}, stars={d.stars}, category={d.repo_category.value})",
        f"Description: {d.description or 'N/A'}",
        f"Use-case tags: {', '.join(d.use_case_tags) or 'N/A'}",
        f"Matched files: {', '.join(d.matched_files[:5]) or 'N/A'}",
    ]
    if d.code_snippets:
        lines.append("Code evidence:")
        for s in d.code_snippets[:3]:
            lines.append(f"  [{s.file_path}:{s.line_no}] ({s.match_type})")
            lines.append(f"  ```python\n{s.snippet}\n  ```")
    return "\n".join(lines)


def _github_models_summary(library: str, digests: list[RepoDigest]) -> str:
    import httpx

    digest_text = "\n\n".join(_format_digest_for_llm(d) for d in digests)

    prompt = (
        f"You are a senior engineer writing a concise synthesis for a library-usage report.\n\n"
        f"Library: {library}\n\nTop repos with code evidence:\n{digest_text}\n\n"
        f"Write a 400-word synthesis covering: common use-cases, patterns, tips for juniors, "
        f"mistakes to avoid, and 3 next-project ideas. Use markdown headers.\n\n"
        f"IMPORTANT RULES:\n"
        f"- Every claim about how {library} is used must cite a specific repo name and file path "
        f"from the evidence above.\n"
        f"- If you cannot cite evidence for a claim, write: "
        f"'No direct code evidence available for this claim.'\n"
        f"- Do not infer usage patterns from descriptions or topic tags alone.\n"
        f"- Do not invent file names or snippet content."
    )

    r = httpx.post(
        f"{GITHUB_MODELS_API}/chat/completions",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "model": GITHUB_MODELS_MODEL,
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def summarize(library: str, digests: list[RepoDigest]) -> str:
    if llm_available():
        try:
            return _github_models_summary(library, digests)
        except Exception as e:
            print(f"[warn] GitHub Models summary failed ({e}), using template fallback")
    return _template_summary(library, digests)
