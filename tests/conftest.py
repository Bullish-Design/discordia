# tests/conftest.py
from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    """Ensure the src/ layout package is importable when running tests."""

    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
