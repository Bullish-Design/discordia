# tests/test_project_structure.py
from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_text(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def test_required_directories_exist() -> None:
    root = _project_root()
    required_dirs = [
        "src",
        "src/discordia",
        "src/discordia/models",
        "src/discordia/managers",
        "src/discordia/persistence",
        "src/discordia/llm",
        "tests",
    ]
    for d in required_dirs:
        assert (root / d).is_dir(), f"Missing directory: {d}"


def test_init_files_exist_and_have_headers() -> None:
    root = _project_root()
    init_files = [
        "src/discordia/__init__.py",
        "src/discordia/models/__init__.py",
        "src/discordia/managers/__init__.py",
        "src/discordia/persistence/__init__.py",
        "src/discordia/llm/__init__.py",
        "tests/__init__.py",
    ]

    for rel in init_files:
        path = root / rel
        assert path.is_file(), f"Missing file: {rel}"
        content = path.read_text(encoding="utf-8").splitlines()
        assert content, f"Empty file: {rel}"
        assert content[0].strip() == f"# {rel}", f"Bad header in {rel}: {content[0]!r}"
        assert len(content) >= 2, f"Missing future import in {rel}"
        assert content[1].strip() == "from __future__ import annotations", f"Bad future import in {rel}"

    pkg_init = _read_text(root, "src/discordia/__init__.py")
    assert '__version__ = "0.1.0"' in pkg_init
    assert "__all__" in pkg_init


def test_pyproject_toml_has_required_config() -> None:
    root = _project_root()
    pyproject_path = root / "pyproject.toml"
    assert pyproject_path.is_file(), "Missing pyproject.toml"

    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data["project"]

    assert project["name"] == "discordia"
    assert project["version"] == "0.1.0"
    assert project["requires-python"] == ">=3.11"

    deps = set(project.get("dependencies", []))
    required_deps = {
        "interactions.py>=5.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "sqlmodel>=0.0.14",
        "mirascope>=1.0.0",
        "aiofiles>=23.0.0",
        "python-dotenv>=1.0.0",
        "aiosqlite>=0.19.0",
    }
    # print(f"\n\nDependencies found: \n{sorted(deps)}\n")
    missing = required_deps - deps
    assert not missing, f"Missing dependencies: {sorted(missing)}"

    dev = set(project.get("optional-dependencies", {}).get("dev", []))
    required_dev = {
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.0.0",
        "mypy>=1.5.0",
        "ruff>=0.1.0",
    }
    # print(f"\n\nOptional Dependencies (dev) found: \n{sorted(dev)}\n\n")
    missing_dev = required_dev - dev
    assert not missing_dev, f"Missing dev dependencies: {sorted(missing_dev)}"

    ruff = data["tool"]["ruff"]
    assert ruff["line-length"] == 120
    assert ruff["select"] == ["E", "F", "I"]
    assert ruff["ignore"] == []

    mypy = data["tool"]["mypy"]
    assert mypy["strict"] is True
    assert mypy["python_version"] == "3.11"

    pytest_cfg = data["tool"]["pytest"]["ini_options"]
    assert pytest_cfg["asyncio_mode"] == "auto"


def test_version_string_is_accessible() -> None:
    root = _project_root()
    src = root / "src"
    sys.path.insert(0, str(src))
    import discordia  # noqa: E402

    assert discordia.__version__ == "0.1.0"
