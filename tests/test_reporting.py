import tempfile
from pathlib import Path

import pytest

from libexplorer.models import RepoDigest


@pytest.fixture
def sample_digests() -> list[RepoDigest]:
    return [
        RepoDigest(
            full_name="alice/retry-service",
            html_url="https://github.com/alice/retry-service",
            description="A service using tenacity for retry logic",
            stars=250,
            language="Python",
            topics=["retry", "python"],
            license="MIT",
            score=0.812,
            evidence_summary={"imports": 3, "decorators": 2, "function_calls": 5},
            readme_snippet="Uses tenacity to handle transient failures gracefully.",
            matched_files=["src/client.py", "src/worker.py"],
            use_case_tags=["retry", "web"],
        ),
        RepoDigest(
            full_name="bob/async-scraper",
            html_url="https://github.com/bob/async-scraper",
            description="Async web scraper",
            stars=87,
            language="Python",
            topics=["scraping", "async"],
            license="Apache-2.0",
            score=0.654,
            evidence_summary={"imports": 1, "decorators": 0, "function_calls": 4},
            readme_snippet=None,
            matched_files=["scraper/core.py"],
            use_case_tags=["async", "web"],
        ),
    ]


def test_jinja2_render_produces_markdown(sample_digests, tmp_path, monkeypatch):
    from libexplorer import reporting
    from libexplorer.config import TEMPLATES_DIR

    # Patch report output dir to tmp
    monkeypatch.setattr(reporting, "lib_report_dir", lambda lib: tmp_path)

    out = reporting.render("tenacity", sample_digests, "## Synthesis\nGreat library.")
    assert out.exists()
    content = out.read_text()

    assert "# Library Usage Report: `tenacity`" in content
    assert "alice/retry-service" in content
    assert "bob/async-scraper" in content
    assert "0.812" in content
    assert "Synthesis" in content


def test_repo_names_appear_in_table(sample_digests, tmp_path, monkeypatch):
    from libexplorer import reporting

    monkeypatch.setattr(reporting, "lib_report_dir", lambda lib: tmp_path)

    out = reporting.render("tenacity", sample_digests, "synthesis text")
    content = out.read_text()

    assert "alice/retry-service" in content
    assert "bob/async-scraper" in content


def test_readme_snippet_included_when_present(sample_digests, tmp_path, monkeypatch):
    from libexplorer import reporting

    monkeypatch.setattr(reporting, "lib_report_dir", lambda lib: tmp_path)

    out = reporting.render("tenacity", sample_digests, "")
    content = out.read_text()

    assert "transient failures gracefully" in content


def test_synthesis_included_verbatim(sample_digests, tmp_path, monkeypatch):
    from libexplorer import reporting

    monkeypatch.setattr(reporting, "lib_report_dir", lambda lib: tmp_path)
    synthesis = "## My Synthesis\nSome unique text 12345."

    out = reporting.render("tenacity", sample_digests, synthesis)
    content = out.read_text()

    assert "Some unique text 12345." in content


def test_empty_digests_renders_without_error(tmp_path, monkeypatch):
    from libexplorer import reporting

    monkeypatch.setattr(reporting, "lib_report_dir", lambda lib: tmp_path)

    out = reporting.render("somelib", [], "No repos found.")
    assert out.exists()
    content = out.read_text()
    assert "somelib" in content
