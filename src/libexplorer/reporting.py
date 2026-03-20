from __future__ import annotations

from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import TEMPLATES_DIR, lib_report_dir
from .models import RepoDigest


def render(library: str, digests: list[RepoDigest], synthesis: str) -> Path:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape([]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("final_report.md.j2")

    report_dir = lib_report_dir(library)
    out_path = report_dir / "final_report.md"

    content = template.render(
        library=library,
        digests=digests,
        synthesis=synthesis,
        generated_date=date.today().isoformat(),
        total_repos=len(digests),
    )
    out_path.write_text(content)
    return out_path
