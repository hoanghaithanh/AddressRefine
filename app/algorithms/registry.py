"""Registry of available `MatchingAlgorithm` implementations.

Adding a new algorithm means instantiating it here and adding it to
`_ALGORITHMS` — no other module needs to change to pick it up (routers and
`matching_service` only ever go through `list_algorithms`/`get_algorithm`).
"""

from __future__ import annotations

from app.algorithms.base import MatchingAlgorithm
from app.algorithms.fingerprint import FingerprintAlgorithm, NGramFingerprintAlgorithm
from app.algorithms.nearest_neighbor import LevenshteinNNAlgorithm, NCDAlgorithm

_ALGORITHMS: list[MatchingAlgorithm] = [
    FingerprintAlgorithm(),
    NGramFingerprintAlgorithm(),
    LevenshteinNNAlgorithm(),
    NCDAlgorithm(),
]

_ALGORITHMS_BY_KEY: dict[str, MatchingAlgorithm] = {algo.key: algo for algo in _ALGORITHMS}


def list_algorithms() -> list[MatchingAlgorithm]:
    """Return all registered algorithm instances, in registration order."""
    return list(_ALGORITHMS)


def get_algorithm(key: str) -> MatchingAlgorithm | None:
    """Return the registered algorithm instance for `key`, or None if unknown."""
    return _ALGORITHMS_BY_KEY.get(key)
