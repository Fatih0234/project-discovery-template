from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── API keys ──────────────────────────────────────────────────────────────────
# GH_TOKEN is the Codespaces-injected name; GITHUB_TOKEN is the local .env name
GITHUB_TOKEN: str | None = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")

# GitHub Models API — same token, no extra key needed
GITHUB_MODELS_API = "https://models.inference.ai.azure.com"
GITHUB_MODELS_MODEL = "gpt-4o-mini"

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


def llm_available() -> bool:
    return GITHUB_TOKEN is not None
