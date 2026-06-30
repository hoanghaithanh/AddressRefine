"""Tests for app/algorithms/ncd.py — normalized_compression_distance.

Covers AC-M3-7 through AC-M3-10, plus the no-pandas static check (AC-M3-41).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.algorithms.ncd import normalized_compression_distance

# ---------------------------------------------------------------------------
# AC-M3-7 — identical non-empty strings → 0.0
# ---------------------------------------------------------------------------


def test_ncd_identical_strings_returns_zero():
    """AC-M3-7: NCD(a, a) == 0.0 for any non-empty string."""
    assert normalized_compression_distance("hello world", "hello world") == pytest.approx(
        0.0, abs=1e-6
    )


def test_ncd_identical_long_strings_returns_zero():
    """AC-M3-7: NCD(a, a) == 0.0 even for longer strings."""
    s = "123 main street, springfield, usa 00501"
    assert normalized_compression_distance(s, s) == pytest.approx(0.0, abs=1e-6)


# ---------------------------------------------------------------------------
# AC-M3-8 — dissimilar pair > similar pair (relative assertion, per AC revision)
# ---------------------------------------------------------------------------


def test_ncd_dissimilar_pair_greater_than_similar_pair():
    """AC-M3-8: NCD of dissimilar strings is strictly greater than NCD of similar strings.

    AC-M3-8 was revised to use a relative assertion (not an absolute > 0.5 threshold).
    NCD(identical) == 0.0; NCD(dissimilar) must be > 0.0.
    """
    ncd_similar = normalized_compression_distance("hello world", "hello world")
    ncd_dissimilar = normalized_compression_distance("hello world", "xyz abc 123 qwerty")

    assert ncd_dissimilar > ncd_similar


def test_ncd_address_variants_are_more_similar_than_random():
    """AC-M3-8: two address variants should have lower NCD than two unrelated strings."""
    addr_a = "123 main street"
    addr_b = "123 main st"
    unrelated = "zzzzzzzzzzzzzzzzzzzzzzzzzzzz qwerty qwerty qwerty"

    ncd_similar = normalized_compression_distance(addr_a, addr_b)
    ncd_dissimilar = normalized_compression_distance(addr_a, unrelated)

    assert ncd_dissimilar > ncd_similar


# ---------------------------------------------------------------------------
# AC-M3-9 — NCD is symmetric
# ---------------------------------------------------------------------------


def test_ncd_is_symmetric_basic():
    """AC-M3-9: NCD(a, b) == NCD(b, a)."""
    a = "hello world"
    b = "foo bar baz"
    assert normalized_compression_distance(a, b) == pytest.approx(
        normalized_compression_distance(b, a), abs=1e-6
    )


def test_ncd_is_symmetric_address_strings():
    """AC-M3-9: symmetry holds for typical address strings."""
    a = "123 main street springfield"
    b = "456 oak avenue shelbyville"
    assert normalized_compression_distance(a, b) == pytest.approx(
        normalized_compression_distance(b, a), abs=1e-6
    )


def test_ncd_is_symmetric_mixed_lengths():
    """AC-M3-9: symmetry holds even when strings have very different lengths."""
    a = "a"
    b = "a" * 100
    assert normalized_compression_distance(a, b) == pytest.approx(
        normalized_compression_distance(b, a), abs=1e-6
    )


# ---------------------------------------------------------------------------
# AC-M3-10 — both empty strings → 0.0
# ---------------------------------------------------------------------------


def test_ncd_both_empty_strings_returns_zero():
    """AC-M3-10: NCD('', '') == 0.0."""
    assert normalized_compression_distance("", "") == pytest.approx(0.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Additional in-range check (NCD values should be in [0.0, ~1.0])
# ---------------------------------------------------------------------------


def test_ncd_value_is_non_negative():
    """NCD must be >= 0 for any pair of strings."""
    a = "abc def ghi"
    b = "xyz uvw rst"
    assert normalized_compression_distance(a, b) >= 0.0


def test_ncd_value_is_at_most_approximately_1():
    """NCD is normally in [0, 1] (may slightly exceed 1.0 due to compressor
    overhead, but should not be wildly out of range)."""
    a = "hello world"
    b = "qwerty asdf"
    result = normalized_compression_distance(a, b)
    # Allow slight overshoot (per docstring) but catch clearly wrong values.
    assert result < 2.0


# ---------------------------------------------------------------------------
# AC-M3-41 — no pandas import in ncd.py
# ---------------------------------------------------------------------------


def test_ncd_module_does_not_import_pandas():
    """AC-M3-41: ncd.py must not import pandas (static AST check)."""
    ncd_path = Path(__file__).resolve().parents[2] / "app" / "algorithms" / "ncd.py"
    source = ncd_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(alias.name.split(".")[0] == "pandas" for alias in node.names), (
                "ncd.py must not import pandas"
            )
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                assert node.module.split(".")[0] != "pandas", "ncd.py must not import pandas"
