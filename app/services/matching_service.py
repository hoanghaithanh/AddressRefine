"""Matching orchestration: runs the session's chosen algorithm and rebuilds
`session.candidate_pairs`.

This module never imports `pandas` or touches a frame directly — addresses
are obtained exclusively via `ComputeBackend.extract_street_addresses`, per
the `compute/` vs `algorithms/` seam documented in `CLAUDE.md`.
"""

from __future__ import annotations

from app.algorithms.registry import get_algorithm
from app.compute import get_compute_backend
from app.models.domain import CandidatePair, Session


def run_matching(session: Session) -> None:
    """Run the session's selected algorithm and replace `session.candidate_pairs`.

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
    addresses = backend.extract_street_addresses(frame, session.mapping)

    output = algorithm.run(addresses, None, session.algorithm_params)

    # Each multi-row cluster becomes exactly one CandidatePair, never raw
    # pairwise combinations -- consistent with the clusters-not-pairs
    # rendering model.
    session.candidate_pairs = [
        CandidatePair(row_indices=sorted(row_indices), distance=None)
        for row_indices in output.clusters.values()
    ]
