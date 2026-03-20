import re

import pytest

from libexplorer.verification import _count_evidence


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
