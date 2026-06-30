"""Nearest-neighbor matching algorithms: Levenshtein Distance and PPM/NCD.

Both algorithms:
1. Use `blocks` (from `compute_blocks`) to restrict pairwise comparisons to
   rows in the same block — comparisons across blocks are never performed.
2. Produce `AlgorithmOutput.pairs` (list of `(row_i, row_j, distance)`) instead
   of `AlgorithmOutput.clusters`.

Neither algorithm imports `pandas` or touches a DataFrame. They operate purely
on `dict[int, str]` address maps handed by `app/services/matching_service.py`.
"""

from __future__ import annotations

from typing import Any

from rapidfuzz.distance import Levenshtein

from app.algorithms.base import AlgorithmFamily, AlgorithmOutput, MatchingAlgorithm, ParamSpec
from app.algorithms.ncd import normalized_compression_distance


class LevenshteinNNAlgorithm(MatchingAlgorithm):
    """Nearest-neighbor algorithm using Levenshtein (edit) distance.

    Pairs rows whose street-address Levenshtein distance is <= `threshold`.
    Uses `rapidfuzz.distance.Levenshtein.distance` with `score_cutoff=threshold`
    for efficiency: rapidfuzz returns `threshold + 1` (i.e. above cutoff) when
    the true distance exceeds the cutoff, avoiding full DP computation for
    clearly dissimilar pairs.

    `threshold=0` is valid and matches only identical strings.
    """

    key = "levenshtein"
    label = "Levenshtein Distance"
    family = AlgorithmFamily.NEAREST_NEIGHBOR
    param_specs: list[ParamSpec] = [
        ParamSpec(name="threshold", label="Max edit distance", param_type=int, default=3),
    ]

    def run(
        self,
        addresses: dict[int, str],
        blocks: dict[str, list[int]] | None,
        params: dict[str, Any],
    ) -> AlgorithmOutput:
        threshold: int = params.get("threshold", self.param_specs[0].default)

        pairs: list[tuple[int, int, float]] = []

        if blocks is None:
            # Fallback: compare all rows against each other (should not happen
            # in normal usage — matching_service always provides blocks for NN).
            row_list = list(addresses.keys())
            for i, row_i in enumerate(row_list):
                for row_j in row_list[i + 1 :]:
                    dist = Levenshtein.distance(
                        addresses[row_i], addresses[row_j], score_cutoff=threshold
                    )
                    if dist <= threshold:
                        pairs.append((row_i, row_j, float(dist)))
        else:
            for block_indices in blocks.values():
                for i in range(len(block_indices)):
                    for j in range(i + 1, len(block_indices)):
                        row_i = block_indices[i]
                        row_j = block_indices[j]
                        dist = Levenshtein.distance(
                            addresses[row_i], addresses[row_j], score_cutoff=threshold
                        )
                        if dist <= threshold:
                            pairs.append((row_i, row_j, float(dist)))

        return AlgorithmOutput(clusters={}, pairs=pairs)


class NCDAlgorithm(MatchingAlgorithm):
    """Nearest-neighbor algorithm using Normalized Compression Distance (PPM/NCD).

    The UI exposes `threshold` as an integer in [1, 10]. Internally this is
    scaled to a float cutoff: `internal_cutoff = ui_threshold / 10.0`. For
    example, `threshold=3` → internal cutoff `0.3`; `threshold=10` → cutoff
    `1.0` (effectively no filtering). Validation that `threshold` is in [1, 10]
    is performed in the router, not here.

    Pairs rows whose NCD score is <= `internal_cutoff`.
    """

    key = "ncd"
    label = "PPM / NCD"
    family = AlgorithmFamily.NEAREST_NEIGHBOR
    param_specs: list[ParamSpec] = [
        ParamSpec(name="threshold", label="Similarity threshold (1–10)", param_type=int, default=3),
    ]

    def run(
        self,
        addresses: dict[int, str],
        blocks: dict[str, list[int]] | None,
        params: dict[str, Any],
    ) -> AlgorithmOutput:
        ui_threshold: int = params.get("threshold", self.param_specs[0].default)
        # Scale UI integer threshold to internal NCD float cutoff.
        # E.g. ui_threshold=3 → internal_cutoff=0.3 (meaning pairs with NCD
        # score <= 0.3 are considered matches).
        internal_cutoff: float = ui_threshold / 10.0

        pairs: list[tuple[int, int, float]] = []

        if blocks is None:
            # Fallback: compare all rows (should not happen in normal usage).
            row_list = list(addresses.keys())
            for i, row_i in enumerate(row_list):
                for row_j in row_list[i + 1 :]:
                    score = normalized_compression_distance(addresses[row_i], addresses[row_j])
                    if score <= internal_cutoff:
                        pairs.append((row_i, row_j, score))
        else:
            for block_indices in blocks.values():
                for i in range(len(block_indices)):
                    for j in range(i + 1, len(block_indices)):
                        row_i = block_indices[i]
                        row_j = block_indices[j]
                        score = normalized_compression_distance(addresses[row_i], addresses[row_j])
                        if score <= internal_cutoff:
                            pairs.append((row_i, row_j, score))

        return AlgorithmOutput(clusters={}, pairs=pairs)
