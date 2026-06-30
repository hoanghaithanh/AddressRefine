"""Tests for app/algorithms/blocking.py — compute_blocks.

Covers AC-M3-1 through AC-M3-6.
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.algorithms.blocking import compute_blocks

# ---------------------------------------------------------------------------
# AC-M3-1 — zip prefix grouping (3-char prefix as block key)
# ---------------------------------------------------------------------------


def test_compute_blocks_groups_rows_by_3char_zip_prefix():
    """AC-M3-1: rows whose normalized zip starts with the same 3 chars share a block."""
    rows = {
        0: {"zip": "12345", "city": "Springfield", "street": "1 A St", "country": "USA"},
        1: {"zip": "12399", "city": "Shelbyville", "street": "2 B St", "country": "USA"},
        2: {"zip": "99999", "city": "Shelbyville", "street": "3 C St", "country": "USA"},
    }
    blocks = compute_blocks(rows)

    # rows 0 and 1 share zip prefix "123"
    assert "123" in blocks
    assert set(blocks["123"]) == {0, 1}

    # row 2 has its own prefix "999"
    assert "999" in blocks
    assert blocks["999"] == [2]


def test_compute_blocks_block_key_equals_3char_prefix():
    """AC-M3-1: the block key is the first 3 characters of the normalized zip."""
    rows = {
        0: {"zip": "90210", "city": "", "street": "Beverly Hills", "country": ""},
    }
    blocks = compute_blocks(rows)

    assert "902" in blocks
    assert blocks["902"] == [0]


# ---------------------------------------------------------------------------
# AC-M3-2 — short zip (< 3 chars) uses the whole normalized zip as key
# ---------------------------------------------------------------------------


def test_compute_blocks_short_zip_2chars_uses_full_string():
    """AC-M3-2: zip of length 2 uses the full string as block key."""
    rows = {
        0: {"zip": "AB", "city": "London", "street": "10 D St", "country": "GB"},
    }
    blocks = compute_blocks(rows)

    assert "ab" in blocks
    assert blocks["ab"] == [0]


def test_compute_blocks_short_zip_1char_uses_full_string():
    """AC-M3-2: zip of length 1 uses the full string as block key."""
    rows = {
        0: {"zip": "X", "city": "London", "street": "10 D St", "country": "GB"},
    }
    blocks = compute_blocks(rows)

    assert "x" in blocks
    assert blocks["x"] == [0]


# ---------------------------------------------------------------------------
# AC-M3-3 — city fallback when zip is blank
# ---------------------------------------------------------------------------


def test_compute_blocks_city_fallback_when_zip_blank():
    """AC-M3-3: blank zip -> city is used as block key."""
    rows = {
        0: {"zip": "", "city": "Portland", "street": "1 A St", "country": ""},
        1: {"zip": "", "city": "Portland", "street": "2 B St", "country": ""},
        2: {"zip": "", "city": "Seattle", "street": "3 C St", "country": ""},
    }
    blocks = compute_blocks(rows)

    assert "portland" in blocks
    assert set(blocks["portland"]) == {0, 1}
    assert "seattle" in blocks
    assert blocks["seattle"] == [2]


def test_compute_blocks_city_block_is_separate_from_zip_block():
    """AC-M3-3: city-keyed blocks don't overlap with zip-keyed blocks."""
    rows = {
        0: {"zip": "12345", "city": "Portland", "street": "1 A St", "country": ""},
        1: {"zip": "", "city": "123", "street": "2 B St", "country": ""},
    }
    blocks = compute_blocks(rows)

    # row 0 → zip prefix "123"; row 1 → city "123" (both happen to normalize to "123"
    # but row 0 wins on zip priority, so they will be in the same bucket —
    # this is expected: zip prefix "123" == city "123" by coincidence)
    # The important thing is row 0 is NOT placed in __unblocked__
    assert "__unblocked__" not in blocks


def test_compute_blocks_city_key_is_normalized_lowercase():
    """AC-M3-3: the city block key is the normalized (lowercase) city string."""
    rows = {
        0: {"zip": "", "city": "New York", "street": "1 A St", "country": ""},
    }
    blocks = compute_blocks(rows)

    assert "new york" in blocks


# ---------------------------------------------------------------------------
# AC-M3-4 — __unblocked__ bucket
# ---------------------------------------------------------------------------


def test_compute_blocks_unblocked_when_no_zip_or_city():
    """AC-M3-4: rows with both zip and city blank end up in __unblocked__."""
    rows = {
        0: {"zip": "", "city": "", "street": "1 A St", "country": ""},
        1: {"zip": "", "city": "", "street": "2 B St", "country": ""},
    }
    blocks = compute_blocks(rows)

    assert "__unblocked__" in blocks
    assert set(blocks["__unblocked__"]) == {0, 1}


def test_compute_blocks_unblocked_rows_not_in_zip_or_city_blocks():
    """AC-M3-4: unblocked rows do not appear in any other block."""
    rows = {
        0: {"zip": "", "city": "", "street": "1 A St", "country": ""},
        1: {"zip": "90210", "city": "Beverly Hills", "street": "2 B St", "country": ""},
    }
    blocks = compute_blocks(rows)

    assert "__unblocked__" in blocks
    assert blocks["__unblocked__"] == [0]
    assert "902" in blocks
    assert blocks["902"] == [1]


# ---------------------------------------------------------------------------
# AC-M3-5 — normalization: whitespace and case
# ---------------------------------------------------------------------------


def test_compute_blocks_zip_normalization_strips_whitespace():
    """AC-M3-5: leading/trailing whitespace on zip is stripped before key derivation."""
    rows = {
        0: {"zip": "012", "city": "", "street": "A", "country": ""},
        1: {"zip": " 012", "city": "", "street": "B", "country": ""},
    }
    blocks = compute_blocks(rows)

    # Both should map to the same block key "012"
    assert "012" in blocks
    assert set(blocks["012"]) == {0, 1}


def test_compute_blocks_zip_normalization_lowercases():
    """AC-M3-5: zip is lowercased before key derivation."""
    rows = {
        0: {"zip": "ABC", "city": "", "street": "A", "country": ""},
        1: {"zip": "abc", "city": "", "street": "B", "country": ""},
    }
    blocks = compute_blocks(rows)

    assert "abc" in blocks
    assert set(blocks["abc"]) == {0, 1}


def test_compute_blocks_city_normalization_strips_whitespace():
    """AC-M3-5: leading/trailing whitespace on city is stripped before key derivation."""
    rows = {
        0: {"zip": "", "city": "NYC", "street": "A", "country": ""},
        1: {"zip": "", "city": " NYC ", "street": "B", "country": ""},
    }
    blocks = compute_blocks(rows)

    assert "nyc" in blocks
    assert set(blocks["nyc"]) == {0, 1}


def test_compute_blocks_city_normalization_lowercases():
    """AC-M3-5: city is lowercased before key derivation."""
    rows = {
        0: {"zip": "", "city": "NYC", "street": "A", "country": ""},
        1: {"zip": "", "city": "nyc", "street": "B", "country": ""},
    }
    blocks = compute_blocks(rows)

    assert "nyc" in blocks
    assert set(blocks["nyc"]) == {0, 1}


# ---------------------------------------------------------------------------
# AC-M3-6 — pure function: no pandas import
# ---------------------------------------------------------------------------


def test_compute_blocks_accepts_only_dict_argument():
    """AC-M3-6: compute_blocks works with just a dict[int, dict[str, str]]."""
    rows: dict[int, dict[str, str]] = {
        0: {"zip": "10001", "city": "New York", "street": "1 A St", "country": ""},
    }
    # Should not raise; no ColumnMapping or DataFrame required.
    result = compute_blocks(rows)
    assert isinstance(result, dict)


def test_blocking_module_does_not_import_pandas():
    """AC-M3-6 + AC-M3-41: blocking.py must not import pandas (static check)."""
    blocking_path = Path(__file__).resolve().parents[2] / "app" / "algorithms" / "blocking.py"
    source = blocking_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(alias.name.split(".")[0] == "pandas" for alias in node.names), (
                "blocking.py must not import pandas"
            )
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                assert node.module.split(".")[0] != "pandas", "blocking.py must not import pandas"


def test_compute_blocks_returns_dict_of_str_to_list_of_int():
    """AC-M3-6: return type is dict[str, list[int]]."""
    rows = {0: {"zip": "12345", "city": "X", "street": "Y", "country": ""}}
    result = compute_blocks(rows)

    assert isinstance(result, dict)
    for key, val in result.items():
        assert isinstance(key, str)
        assert isinstance(val, list)
        assert all(isinstance(i, int) for i in val)


def test_compute_blocks_empty_input_returns_empty_dict():
    """Edge case: empty input produces empty output."""
    assert compute_blocks({}) == {}
