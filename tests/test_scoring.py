from datetime import datetime, timezone

import pytest

from libexplorer.models import CandidateRepo, VerifiedRepo
from libexplorer.scoring import (
    WEIGHTS,
    _evidence_score,
    _learnability_score,
    _popularity_score,
    _quality_score,
    _readme_score,
    _recency_score,
    score_repo,
)


def make_verified(
    stars: int = 100,
    import_count: int = 5,
    decorator_count: int = 0,
    function_call_count: int = 3,
    matched_files: list[str] | None = None,
    readme_snippet: str | None = "Uses tenacity for retry logic",
    pushed_at: datetime | None = None,
    license: str | None = "MIT",
    topics: list[str] | None = None,
) -> VerifiedRepo:
    candidate = CandidateRepo(
        full_name="user/repo",
        html_url="https://github.com/user/repo",
        stargazers_count=stars,
        pushed_at=pushed_at or datetime.now(timezone.utc),
        license=license,
        topics=topics if topics is not None else ["python", "retry"],
    )
    return VerifiedRepo(
        candidate=candidate,
        import_count=import_count,
        decorator_count=decorator_count,
        function_call_count=function_call_count,
        matched_files=matched_files if matched_files is not None else ["src/utils.py", "tests/test_utils.py"],
        readme_snippet=readme_snippet,
    )


def test_evidence_score_zero_when_no_evidence():
    v = make_verified(import_count=0, decorator_count=0, function_call_count=0)
    assert _evidence_score(v) == 0.0


def test_evidence_score_caps_at_one():
    v = make_verified(import_count=100, decorator_count=50, function_call_count=50)
    assert _evidence_score(v) == 1.0


def test_evidence_score_proportional():
    v = make_verified(import_count=10, decorator_count=0, function_call_count=0)
    assert _evidence_score(v) == pytest.approx(0.5)


def test_learnability_zero_no_files():
    v = make_verified(matched_files=[])
    assert _learnability_score(v) == 0.0


def test_learnability_caps_at_one():
    v = make_verified(matched_files=["a", "b", "c", "d", "e", "f", "g"])
    assert _learnability_score(v) == 1.0


def test_quality_score_with_license_and_topics():
    v = make_verified(license="MIT", topics=["python", "retry", "http"])
    q = _quality_score(v)
    assert 0.0 < q <= 1.0


def test_quality_score_no_license():
    v = make_verified(license=None, topics=[])
    # No license, no topics → only issues component
    q = _quality_score(v)
    assert q >= 0.0


def test_recency_recent_repo():
    v = make_verified(pushed_at=datetime.now(timezone.utc))
    assert _recency_score(v) == 1.0


def test_recency_old_repo():
    from datetime import timedelta
    old = datetime.now(timezone.utc) - timedelta(days=800)
    v = make_verified(pushed_at=old)
    assert _recency_score(v) == 0.0


def test_popularity_low_stars():
    v = make_verified(stars=0)
    assert _popularity_score(v) == 0.0


def test_popularity_high_stars():
    v = make_verified(stars=50000)
    assert _popularity_score(v) == 1.0


def test_readme_score_present():
    v = make_verified(readme_snippet="Uses tenacity")
    assert _readme_score(v) == 1.0


def test_readme_score_absent():
    v = make_verified(readme_snippet=None)
    assert _readme_score(v) == 0.0


def test_score_repo_returns_weighted_sum():
    v = make_verified()
    scored = score_repo(v)
    assert 0.0 <= scored.score <= 1.0
    assert set(scored.score_breakdown.keys()) == set(WEIGHTS.keys())


def test_score_repo_all_zeros():
    v = make_verified(
        import_count=0, decorator_count=0, function_call_count=0,
        matched_files=[], readme_snippet=None, stars=0,
        pushed_at=datetime(2010, 1, 1, tzinfo=timezone.utc),
        license=None, topics=[],
    )
    scored = score_repo(v)
    assert scored.score == pytest.approx(0.0)


def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)
