"""Key-collision matching algorithms: Fingerprint and N-Gram Fingerprint.

Both algorithms derive a normalized "key" per row and cluster rows that
share an identical key. Neither imports `pandas` or touches a DataFrame —
they operate purely on the `dict[int, str]` address map handed to them by
`app/services/matching_service.py`.
"""

from __future__ import annotations

import re
import string
from typing import Any

from app.algorithms.base import AlgorithmFamily, AlgorithmOutput, MatchingAlgorithm, ParamSpec

_PUNCTUATION_TABLE = str.maketrans({char: " " for char in string.punctuation})
_WHITESPACE_RE = re.compile(r"\s+")


def _strip_punctuation_and_lower(value: str) -> str:
    """Lowercase `value` and replace punctuation characters with spaces."""
    return value.lower().translate(_PUNCTUATION_TABLE)


def _build_clusters(keys_by_row: dict[int, str]) -> dict[str, list[int]]:
    """Group row indices by identical key, dropping singleton keys.

    Rows whose key is `None` (excluded from clustering, e.g. blank address
    or too-short string) are never included.
    """
    rows_by_key: dict[str, list[int]] = {}
    for row_index, key in keys_by_row.items():
        rows_by_key.setdefault(key, []).append(row_index)
    return {key: rows for key, rows in rows_by_key.items() if len(rows) >= 2}


class FingerprintAlgorithm(MatchingAlgorithm):
    """Key-collision algorithm using the classic OpenRefine-style fingerprint.

    Normalization: lowercase, strip punctuation, collapse whitespace, split
    into tokens, dedupe + sort the tokens, then join with a single space.
    Blank/whitespace-only addresses are excluded from clustering, as are
    singleton keys (no other row shares them).
    """

    key = "fingerprint"
    label = "Fingerprint"
    family = AlgorithmFamily.KEY_COLLISION
    param_specs: list[ParamSpec] = []

    def _fingerprint_key(self, address: str) -> str | None:
        normalized = _strip_punctuation_and_lower(address)
        normalized = _WHITESPACE_RE.sub(" ", normalized).strip()
        if not normalized:
            return None
        tokens = sorted(set(normalized.split(" ")))
        return " ".join(tokens)

    def run(
        self,
        addresses: dict[int, str],
        blocks: dict[str, list[int]] | None,
        params: dict[str, Any],
    ) -> AlgorithmOutput:
        keys_by_row: dict[int, str] = {}
        for row_index, address in addresses.items():
            key = self._fingerprint_key(address)
            if key is not None:
                keys_by_row[row_index] = key
        return AlgorithmOutput(clusters=_build_clusters(keys_by_row), pairs=None)


class NGramFingerprintAlgorithm(MatchingAlgorithm):
    """Key-collision algorithm using character n-grams of the normalized address.

    Normalization: lowercase, strip punctuation, then remove all spaces.
    The key is built from all character n-grams of the resulting string,
    deduplicated and sorted, joined with a hyphen (`"-"`) delimiter.
    Strings shorter than `n` characters (after normalization) are excluded
    from clustering, as are singleton keys.
    """

    key = "ngram_fingerprint"
    label = "N-Gram Fingerprint"
    family = AlgorithmFamily.KEY_COLLISION
    param_specs: list[ParamSpec] = [
        ParamSpec(name="n", label="N-Gram size", param_type=int, default=2),
    ]

    def _ngram_key(self, address: str, n: int) -> str | None:
        normalized = _strip_punctuation_and_lower(address)
        normalized = _WHITESPACE_RE.sub("", normalized)
        if len(normalized) < n:
            return None
        ngrams = {normalized[i : i + n] for i in range(len(normalized) - n + 1)}
        return "-".join(sorted(ngrams))

    def run(
        self,
        addresses: dict[int, str],
        blocks: dict[str, list[int]] | None,
        params: dict[str, Any],
    ) -> AlgorithmOutput:
        n = params.get("n", self.param_specs[0].default)
        keys_by_row: dict[int, str] = {}
        for row_index, address in addresses.items():
            key = self._ngram_key(address, n)
            if key is not None:
                keys_by_row[row_index] = key
        return AlgorithmOutput(clusters=_build_clusters(keys_by_row), pairs=None)
