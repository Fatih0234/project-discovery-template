from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import TEMPLATES_DIR, lib_data_dir, lib_report_dir
from .models import RepoDigest


def render(library: str, digests: list[RepoDigest], synthesis: str) -> Path:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape([]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # Add 'in' test for selectattr filtering by list membership
    env.tests["in"] = lambda value, collection: value in collection

    template = env.get_template("final_report.md.j2")

    report_dir = lib_report_dir(library)
    out_path = report_dir / "final_report.md"

    # Load rejected candidates if available (written by scoring step)
    rejected_path = lib_data_dir(library) / "rejected_candidates.json"
    rejected: list[dict] = []
    if rejected_path.exists():
        try:
            rejected = json.loads(rejected_path.read_text())
        except Exception:
            pass

    content = template.render(
        library=library,
        digests=digests,
        synthesis=synthesis,
        generated_date=date.today().isoformat(),
        total_repos=len(digests),
        rejected=rejected,
    )
    out_path.write_text(content)
    return out_path
