# tests/conftest.py
from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    """Ensure the src/ directory is importable during tests."""
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    sys.path.insert(0, str(src))
