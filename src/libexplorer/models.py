from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RepoCategory(str, Enum):
    LIBRARY_SELF = "library_self"
    WRAPPER = "wrapper"
    TUTORIAL = "tutorial"
    APP = "app"
    UNKNOWN = "unknown"


class CodeSnippet(BaseModel):
    file_path: str
    line_no: int
    snippet: str
    match_type: Literal["import", "decorator", "call"]


class CandidateRepo(BaseModel):
    full_name: str
    html_url: str
    description: str | None = None
    stargazers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    pushed_at: datetime | None = None
    language: str | None = None
    topics: list[str] = Field(default_factory=list)
    license: str | None = None


class VerifiedRepo(BaseModel):
    candidate: CandidateRepo
    import_count: int = 0
    decorator_count: int = 0
    function_call_count: int = 0
    matched_files: list[str] = Field(default_factory=list)
    readme_snippet: str | None = None
    code_snippets: list[CodeSnippet] = Field(default_factory=list)

    @property
    def total_evidence(self) -> int:
        return self.import_count + self.decorator_count + self.function_call_count


class ScoredRepo(BaseModel):
    verified: VerifiedRepo
    score: float
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class RepoDigest(BaseModel):
    full_name: str
    html_url: str
    description: str | None = None
    stars: int
    language: str | None
    topics: list[str]
    license: str | None
    score: float
    evidence_summary: dict[str, int]
    readme_snippet: str | None
    matched_files: list[str]
    use_case_tags: list[str] = Field(default_factory=list)
    code_snippets: list[CodeSnippet] = Field(default_factory=list)
    repo_category: RepoCategory = RepoCategory.UNKNOWN


class AnalysisConfig(BaseModel):
    library: str
    language: str = "python"
    top_k: int = 5
    min_stars: int = 10
    max_candidates: int = 50
    skip_cache: bool = False
    llm_provider: str | None = None  # "anthropic" | "openai" | None
    extra: dict[str, Any] = Field(default_factory=dict)
