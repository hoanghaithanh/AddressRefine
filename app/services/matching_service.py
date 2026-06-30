"""Matching orchestration: runs the session's chosen algorithm and rebuilds
`session.candidate_pairs`.

This module never imports `pandas` or touches a frame directly — addresses
are obtained exclusively via `ComputeBackend.extract_street_addresses` (for
key-collision algorithms) or `ComputeBackend.extract_columns` + `compute_blocks`
(for nearest-neighbor algorithms), per the `compute/` vs `algorithms/` seam
documented in `CLAUDE.md`.
"""

from __future__ import annotations

import itertools
import uuid

from app.algorithms.base import AlgorithmFamily
from app.algorithms.blocking import compute_blocks
from app.algorithms.registry import get_algorithm
from app.compute import get_compute_backend
from app.models.domain import CandidatePair, Session


def run_matching(session: Session) -> None:
    """Run the session's selected algorithm and replace `session.candidate_pairs`.

    Key-collision path (Fingerprint, N-Gram Fingerprint):
    - Calls `backend.extract_street_addresses` to get `dict[int, str]`.
    - Calls `algorithm.run(addresses, blocks=None, params)`.
    - Explodes every multi-member cluster in `output.clusters` into one
      `CandidatePair` per pairwise combination (`itertools.combinations`),
      each with `distance=None`.

    Nearest-neighbor path (Levenshtein, NCD):
    - Calls `backend.extract_columns` to get `dict[int, dict[str, str]]`.
    - Passes the result to `compute_blocks` to get `dict[str, list[int]]`.
    - Extracts street addresses separately for the algorithm.
    - Calls `algorithm.run(addresses, blocks, params)`.
    - Maps each `(row_i, row_j, distance)` tuple in `output.pairs` directly
      to one `CandidatePair` — no transitive (union-find) clustering. Each
      pair's `distance` is exactly the value returned for that pair.

    Every `CandidatePair.row_indices` is always exactly length 2, regardless
    of algorithm family (M4).

    Requires `session.mapping` and `session.algorithm_key` to already be set;
    raises `ValueError` if either is missing, or if `algorithm_key` doesn't
    resolve to a registered algorithm. Always rebuilds `candidate_pairs` from
    scratch (no leftover entries from a previous run survive).
    """
    frame = session.current_df
    if frame is None or session.mapping is None:
        raise ValueError("Cannot run matching without an uploaded dataset and confirmed mapping.")

    if session.algorithm_key is None:
        raise ValueError("Cannot run matching without a selected algorithm.")

    algorithm = get_algorithm(session.algorithm_key)
    if algorithm is None:
        raise ValueError(f"Unknown algorithm key: {session.algorithm_key!r}")

    backend = get_compute_backend()

    if algorithm.family == AlgorithmFamily.NEAREST_NEIGHBOR:
        # NN path: need zip+city for blocking, then pass street addresses to algo.
        rows = backend.extract_columns(frame, session.mapping)
        blocks = compute_blocks(rows)
        addresses = backend.extract_street_addresses(frame, session.mapping)

        output = algorithm.run(addresses, blocks, session.algorithm_params)

        session.candidate_pairs = [
            CandidatePair(
                pair_id=str(uuid.uuid4()),
                row_indices=sorted((row_i, row_j)),
                distance=dist,
            )
            for row_i, row_j, dist in (output.pairs or [])
        ]

    else:
        # Key-collision path: explode each multi-member cluster into every
        # pairwise combination, rather than emitting one multi-member entry.
        addresses = backend.extract_street_addresses(frame, session.mapping)
        output = algorithm.run(addresses, None, session.algorithm_params)

        session.candidate_pairs = [
            CandidatePair(
                pair_id=str(uuid.uuid4()),
                row_indices=sorted((row_i, row_j)),
                distance=None,
            )
            for row_indices in output.clusters.values()
            for row_i, row_j in itertools.combinations(sorted(row_indices), 2)
        ]
