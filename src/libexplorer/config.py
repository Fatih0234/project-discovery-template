from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── API keys ──────────────────────────────────────────────────────────────────
GITHUB_TOKEN: str | None = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parents[2]  # project root (above src/)
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"
TEMPLATES_DIR = ROOT_DIR / "templates"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


def lib_data_dir(library: str) -> Path:
    d = DATA_DIR / library
    d.mkdir(parents=True, exist_ok=True)
    return d


def lib_report_dir(library: str) -> Path:
    d = REPORTS_DIR / library
    d.mkdir(parents=True, exist_ok=True)
    return d


def detect_llm_provider() -> str | None:
    if ANTHROPIC_API_KEY:
        return "anthropic"
    if OPENAI_API_KEY:
        return "openai"
    return None
