"""AC-M2-23: no file under app/algorithms/, nor matching_service.py, imports
pandas. This is a static, source-level check rather than a behavioral test --
algorithms must only ever see plain dict[int, str] address maps, never a
DataFrame, per the compute/ vs algorithms/ seam documented in CLAUDE.md.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALGORITHMS_DIR = PROJECT_ROOT / "app" / "algorithms"
MATCHING_SERVICE_FILE = PROJECT_ROOT / "app" / "services" / "matching_service.py"


def _imports_pandas(source: str) -> bool:
    """Return True if `source` contains a top-level or nested `import pandas`
    or `from pandas import ...` statement, via AST inspection (more robust
    than a substring grep against comments/strings mentioning "pandas")."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == "pandas" for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None and node.module.split(".")[0] == "pandas":
                return True
    return False


def _algorithm_files() -> list[Path]:
    return sorted(ALGORITHMS_DIR.glob("*.py"))


@pytest.mark.parametrize("path", _algorithm_files(), ids=lambda p: p.name)
def test_algorithms_file_does_not_import_pandas(path: Path):
    source = path.read_text(encoding="utf-8")

    assert not _imports_pandas(source), f"{path} must not import pandas"


def test_matching_service_does_not_import_pandas():
    source = MATCHING_SERVICE_FILE.read_text(encoding="utf-8")

    assert not _imports_pandas(source), f"{MATCHING_SERVICE_FILE} must not import pandas"


def test_algorithms_dir_has_at_least_the_expected_files():
    """Sanity check that the parametrized glob above isn't silently empty
    (e.g. due to a path typo), which would make the parametrized test
    vacuously pass with zero cases."""
    names = {path.name for path in _algorithm_files()}

    assert {"base.py", "fingerprint.py", "registry.py"}.issubset(names)
