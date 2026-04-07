from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
PROFILES_DIR = DATA_DIR / "profiles"
TARGETS_DIR = DATA_DIR / "targets"
LOGS_DIR = DATA_DIR / "logs"


def ensure_data_dirs() -> None:
    for directory in (DATA_DIR, PROFILES_DIR, TARGETS_DIR, LOGS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
