from __future__ import annotations

import base64
import time
from typing import Any

import httpx

from .config import GITHUB_TOKEN

_BASE = "https://api.github.com"
_HEADERS: dict[str, str] = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    _HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def _get(client: httpx.Client, url: str, params: dict | None = None) -> dict | None:
    for attempt in range(3):
        try:
            r = client.get(url, params=params, headers=_HEADERS, timeout=20)
            if r.status_code == 403 and "rate limit" in r.text.lower():
                wait = int(r.headers.get("Retry-After", 60))
                time.sleep(wait)
                continue
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError:
            return None
        except httpx.RequestError:
            time.sleep(2 ** attempt)
    return None


def search_repos(
    library: str,
    language: str = "python",
    min_stars: int = 10,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Search repos whose name or description mentions the library."""
    query = f"{library} language:{language} stars:>={min_stars}"
    results: list[dict] = []
    page = 1
    with httpx.Client() as client:
        while len(results) < limit:
            data = _get(
                client,
                f"{_BASE}/search/repositories",
                params={"q": query, "sort": "stars", "order": "desc", "per_page": 30, "page": page},
            )
            if not data or not data.get("items"):
                break
            results.extend(data["items"])
            if len(data["items"]) < 30:
                break
            page += 1
    return results[:limit]


def search_repos_by_topic(
    library: str,
    language: str = "python",
    min_stars: int = 10,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Search repos that have the library name as a GitHub topic tag."""
    query = f"topic:{library} language:{language} stars:>={min_stars}"
    with httpx.Client() as client:
        data = _get(
            client,
            f"{_BASE}/search/repositories",
            params={"q": query, "sort": "stars", "order": "desc", "per_page": min(limit, 30)},
        )
    if not data:
        return []
    return data.get("items", [])[:limit]


def search_repos_by_code(
    library: str,
    language: str = "python",
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Search repos via GitHub code search for direct import statements."""
    query = f"import {library} language:{language}"
    with httpx.Client() as client:
        data = _get(
            client,
            f"{_BASE}/search/code",
            params={"q": query, "per_page": min(limit, 30)},
        )
    if not data:
        return []
    # Code search returns file items; extract unique repo objects
    seen: set[str] = set()
    repos: list[dict] = []
    for item in data.get("items", []):
        repo = item.get("repository", {})
        full_name = repo.get("full_name", "")
        if full_name and full_name not in seen:
            seen.add(full_name)
            repos.append(repo)
    return repos[:limit]


def get_repo_metadata(full_name: str) -> dict | None:
    with httpx.Client() as client:
        return _get(client, f"{_BASE}/repos/{full_name}")


def search_code(library: str, full_name: str) -> list[dict[str, Any]]:
    query = f"import {library} repo:{full_name}"
    with httpx.Client() as client:
        data = _get(
            client,
            f"{_BASE}/search/code",
            params={"q": query, "per_page": 20},
        )
    if not data:
        return []
    return data.get("items", [])


def get_readme(full_name: str) -> str | None:
    with httpx.Client() as client:
        data = _get(client, f"{_BASE}/repos/{full_name}/readme")
    if not data:
        return None
    try:
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except Exception:
        return None


def get_file_content(full_name: str, path: str) -> str | None:
    with httpx.Client() as client:
        data = _get(client, f"{_BASE}/repos/{full_name}/contents/{path}")
    if not data:
        return None
    try:
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except Exception:
        return None
