import re

import pytest

from libexplorer.verification import _count_evidence, _extract_snippets, _is_self_repo


def test_import_statement_detected():
    content = "import tenacity\n"
    imp, dec, cal = _count_evidence("tenacity", content)
    assert imp >= 1


def test_from_import_detected():
    content = "from tenacity import retry, stop_after_attempt\n"
    imp, dec, cal = _count_evidence("tenacity", content)
    assert imp >= 1


def test_decorator_detected():
    content = "@tenacity.retry\ndef fetch(): pass\n"
    imp, dec, cal = _count_evidence("tenacity", content)
    assert dec >= 1


def test_function_call_detected():
    content = "tenacity.retry(stop=tenacity.stop_after_attempt(3))\n"
    imp, dec, cal = _count_evidence("tenacity", content)
    assert cal >= 1


def test_no_evidence_in_unrelated_content():
    content = "import os\nimport sys\nprint('hello')\n"
    imp, dec, cal = _count_evidence("tenacity", content)
    assert imp == 0
    assert dec == 0
    assert cal == 0


def test_multiple_imports_counted():
    content = (
        "import tenacity\n"
        "from tenacity import retry\n"
        "from tenacity.stop import stop_after_attempt\n"
    )
    imp, dec, cal = _count_evidence("tenacity", content)
    assert imp >= 2


def test_partial_name_not_matched():
    # "tenacityextra" should not match "tenacity"
    content = "import tenacityextra\n"
    imp, dec, cal = _count_evidence("tenacity", content)
    assert imp == 0


def test_empty_content():
    imp, dec, cal = _count_evidence("tenacity", "")
    assert (imp, dec, cal) == (0, 0, 0)


def test_httpx_import():
    content = "import httpx\nresponse = httpx.get('https://example.com')\n"
    imp, dec, cal = _count_evidence("httpx", content)
    assert imp >= 1
    assert cal >= 1


# --- snippet extraction tests ---

def test_extract_snippets_returns_import_snippet():
    content = "\n".join(["# header", "import tenacity", "x = 1"])
    snippets = _extract_snippets("tenacity", content, "src/app.py")
    assert len(snippets) >= 1
    assert snippets[0].file_path == "src/app.py"
    assert snippets[0].match_type == "import"
    assert "tenacity" in snippets[0].snippet


def test_extract_snippets_caps_per_type():
    # 10 import lines — should cap at max_per_type (default 3)
    lines = [f"import tenacity  # line {i}" for i in range(10)]
    content = "\n".join(lines)
    snippets = _extract_snippets("tenacity", content, "file.py", max_per_type=3)
    import_snippets = [s for s in snippets if s.match_type == "import"]
    assert len(import_snippets) <= 3


def test_extract_snippets_empty_content():
    snippets = _extract_snippets("tenacity", "", "empty.py")
    assert snippets == []


def test_extract_snippets_includes_context_lines():
    lines = ["line1", "line2", "line3", "import tenacity", "line5", "line6", "line7"]
    content = "\n".join(lines)
    snippets = _extract_snippets("tenacity", content, "file.py")
    assert len(snippets) >= 1
    # snippet should include surrounding context
    assert "line2" in snippets[0].snippet or "line5" in snippets[0].snippet


# --- self-repo exclusion tests ---

def test_is_self_repo_exact_match():
    assert _is_self_repo("tenacity", "jd28/tenacity") is True


def test_is_self_repo_case_insensitive():
    assert _is_self_repo("Tenacity", "owner/Tenacity") is True


def test_is_self_repo_normalizes_separators():
    assert _is_self_repo("my-library", "owner/my_library") is True


def test_is_self_repo_false_for_different_name():
    assert _is_self_repo("tenacity", "owner/my-retry-app") is False


def test_is_self_repo_false_for_partial_match():
    assert _is_self_repo("ten", "owner/tenacity") is False
