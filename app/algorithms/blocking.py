"""Zip+city blocking: groups rows into blocks to restrict pairwise comparisons.

Blocking is used by nearest-neighbor algorithms (Levenshtein, NCD) to avoid
O(n²) comparisons across the entire dataset. Each block contains only rows
that share the same geographic "bucket" (first 3 chars of zip, or city),
so pairwise distance is only computed within each block.

This module never imports `pandas` or any other compute-backend type.
It operates purely on the pre-extracted `dict[int, dict[str, str]]` handed
to it by `app/services/matching_service.py`.
"""

from __future__ import annotations


def compute_blocks(rows: dict[int, dict[str, str]]) -> dict[str, list[int]]:
    """Group row indices into blocks by zip prefix or city.

    Block key assignment (in priority order):
    1. If a row's normalized zip (strip + lower) is non-blank, the block key
       is the first 3 characters of the normalized zip (or the whole normalized
       zip if it is shorter than 3 characters).
    2. If the normalized zip is blank but the normalized city is non-blank,
       the block key is the full normalized city string.
    3. If both normalized zip and city are blank, the row is placed in the
       ``"__unblocked__"`` bucket. All such rows share one bucket, which means
       they will be compared pairwise — a potential O(n²) degenerate case when
       most rows lack both zip and city; this is a known v1 trade-off.

    Args:
        rows: Mapping of row index to a dict with at least ``"zip"`` and
            ``"city"`` string values (as returned by
            ``ComputeBackend.extract_columns``). Other keys (``"street"``,
            ``"country"``) are ignored.

    Returns:
        Mapping of block key to the list of row indices in that block.
    """
    blocks: dict[str, list[int]] = {}
    for row_index, cols in rows.items():
        raw_zip = cols.get("zip", "")
        raw_city = cols.get("city", "")

        norm_zip = raw_zip.strip().lower()
        norm_city = raw_city.strip().lower()

        if norm_zip:
            block_key = norm_zip[:3]
        elif norm_city:
            block_key = norm_city
        else:
            block_key = "__unblocked__"

        blocks.setdefault(block_key, []).append(row_index)

    return blocks
