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


def _github_models_summary(library: str, digests: list[RepoDigest]) -> str:
    import httpx

    digest_text = "\n\n".join(
        f"**{d.full_name}** (score={d.score:.2f}, stars={d.stars})\n"
        f"Description: {d.description or 'N/A'}\n"
        f"Use-case tags: {', '.join(d.use_case_tags) or 'N/A'}\n"
        f"Matched files: {', '.join(d.matched_files[:5]) or 'N/A'}"
        for d in digests
    )

    prompt = (
        f"You are a senior engineer writing a concise synthesis for a library-usage report.\n\n"
        f"Library: {library}\n\nTop repos:\n{digest_text}\n\n"
        f"Write a 300-word synthesis covering: common use-cases, patterns, tips for juniors, "
        f"mistakes to avoid, and 3 next-project ideas. Use markdown headers."
    )

    r = httpx.post(
        f"{GITHUB_MODELS_API}/chat/completions",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "model": GITHUB_MODELS_MODEL,
            "max_tokens": 800,
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
