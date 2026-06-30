"""Matching orchestration: runs the session's chosen algorithm and rebuilds
`session.candidate_pairs`.

This module never imports `pandas` or touches a frame directly — addresses
are obtained exclusively via `ComputeBackend.extract_street_addresses` (for
key-collision algorithms) or `ComputeBackend.extract_columns` + `compute_blocks`
(for nearest-neighbor algorithms), per the `compute/` vs `algorithms/` seam
documented in `CLAUDE.md`.
"""

from __future__ import annotations

import uuid

from app.algorithms.base import AlgorithmFamily
from app.algorithms.blocking import compute_blocks
from app.algorithms.registry import get_algorithm
from app.compute import get_compute_backend
from app.models.domain import CandidatePair, Session


class _UnionFind:
    """Minimal union-find (disjoint-set) for clustering row indices.

    Used to merge pairwise matches from nearest-neighbor algorithms into
    transitive clusters: if A-B and B-C are within threshold, all three
    end up in the same cluster.
    """

    def __init__(self) -> None:
        self._parent: dict[int, int] = {}

    def _ensure(self, x: int) -> None:
        if x not in self._parent:
            self._parent[x] = x

    def find(self, x: int) -> int:
        """Return the canonical root of the set containing `x`."""
        self._ensure(x)
        # Path compression.
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])
        return self._parent[x]

    def union(self, x: int, y: int) -> None:
        """Merge the sets containing `x` and `y`."""
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            # Attach ry's tree to rx (simple root assignment; no rank needed
            # at address-CSV scale).
            self._parent[ry] = rx

    def clusters(self) -> dict[int, list[int]]:
        """Return {root: [member, ...]} for all sets with >= 2 members."""
        groups: dict[int, list[int]] = {}
        for node in self._parent:
            root = self.find(node)
            groups.setdefault(root, []).append(node)
        return {root: members for root, members in groups.items() if len(members) >= 2}


def run_matching(session: Session) -> None:
    """Run the session's selected algorithm and replace `session.candidate_pairs`.

    Key-collision path (Fingerprint, N-Gram Fingerprint):
    - Calls `backend.extract_street_addresses` to get `dict[int, str]`.
    - Calls `algorithm.run(addresses, blocks=None, params)`.
    - Converts `output.clusters` to `CandidatePair` list.

    Nearest-neighbor path (Levenshtein, NCD):
    - Calls `backend.extract_columns` to get `dict[int, dict[str, str]]`.
    - Passes the result to `compute_blocks` to get `dict[str, list[int]]`.
    - Extracts street addresses separately for the algorithm.
    - Calls `algorithm.run(addresses, blocks, params)`.
    - Runs union-find on `output.pairs` to form transitive clusters.
    - `CandidatePair.distance` = max pairwise distance within each cluster.

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

        # Build union-find to discover transitive clusters from raw pairs.
        uf = _UnionFind()
        # Track max distance per cluster (keyed by pair of row indices).
        # We record distance for each edge and then find the max within each cluster.
        edge_distances: list[tuple[int, int, float]] = output.pairs or []

        for row_i, row_j, dist in edge_distances:
            uf.union(row_i, row_j)

        cluster_groups = uf.clusters()

        # For each cluster, find the maximum pairwise distance.
        cluster_max_dist: dict[int, float] = {root: 0.0 for root in cluster_groups}
        for row_i, row_j, dist in edge_distances:
            root = uf.find(row_i)
            if root in cluster_max_dist:
                if dist > cluster_max_dist[root]:
                    cluster_max_dist[root] = dist

        session.candidate_pairs = [
            CandidatePair(
                pair_id=str(uuid.uuid4()),
                row_indices=sorted(members),
                distance=cluster_max_dist.get(root, 0.0),
            )
            for root, members in cluster_groups.items()
        ]

    else:
        # Key-collision path: unchanged from M2 behavior.
        addresses = backend.extract_street_addresses(frame, session.mapping)
        output = algorithm.run(addresses, None, session.algorithm_params)

        # Each multi-row cluster becomes exactly one CandidatePair, never raw
        # pairwise combinations — consistent with the clusters-not-pairs
        # rendering model.
        session.candidate_pairs = [
            CandidatePair(
                pair_id=str(uuid.uuid4()),
                row_indices=sorted(row_indices),
                distance=None,
            )
            for row_indices in output.clusters.values()
        ]
