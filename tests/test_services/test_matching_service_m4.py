"""Tests for app/services/matching_service.py — M4 pairwise-only CandidatePair model.

Covers AC-M4-11 through AC-M4-16 from
`docs/ba/acceptance-criteria/m4-merge-review.md`. Supersedes M3's
transitive-clustering/max-pairwise-distance behavior, which M4 deliberately
reverses (see the "M3 reversal" callout at the bottom of that spec).
"""

from __future__ import annotations

import itertools

import pytest

from app.compute.pandas_backend import PandasComputeBackend
from app.models.domain import CandidatePair, ColumnMapping, DatasetVersion, Session
from app.services.matching_service import run_matching


def _make_session(csv_bytes: bytes, mapping: ColumnMapping) -> Session:
    backend = PandasComputeBackend()
    frame = backend.load_csv(csv_bytes)
    session = Session(session_id="test-session")
    session.versions.append(DatasetVersion(version=1, df=frame))
    session.mapping = mapping
    return session


# ---------------------------------------------------------------------------
# AC-M4-11 — a key-collision cluster of 3 explodes into exactly 3 pairs
# ---------------------------------------------------------------------------


def test_key_collision_cluster_of_three_explodes_into_three_pairs():
    """AC-M4-11: three rows whose fingerprint keys are all identical produce
    exactly 3 CandidatePairs (A-B, A-C, B-C), none longer than 2 elements."""
    csv_bytes = b"StreetAddress\n123 Main St\n123 MAIN ST.\n123 main st.\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"

    run_matching(session)

    assert len(session.candidate_pairs) == 3
    pairs_as_sets = {tuple(pair.row_indices) for pair in session.candidate_pairs}
    assert pairs_as_sets == {(0, 1), (0, 2), (1, 2)}
    assert all(len(pair.row_indices) <= 2 for pair in session.candidate_pairs)


def test_ngram_fingerprint_cluster_of_three_explodes_into_three_pairs():
    """AC-M4-11 variant: same behavior for N-Gram Fingerprint."""
    csv_bytes = b"StreetAddress\nabcab\nabcab\nabcab\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "ngram_fingerprint"
    session.algorithm_params = {"n": 2}

    run_matching(session)

    assert len(session.candidate_pairs) == 3
    pairs_as_sets = {tuple(pair.row_indices) for pair in session.candidate_pairs}
    assert pairs_as_sets == {(0, 1), (0, 2), (1, 2)}


# ---------------------------------------------------------------------------
# AC-M4-12 — key-collision pair distance is None
# ---------------------------------------------------------------------------


def test_key_collision_pair_distance_is_none():
    """AC-M4-12: every CandidatePair from a key-collision algorithm has
    distance=None."""
    csv_bytes = b"StreetAddress\n123 Main St\n123 MAIN ST.\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"

    run_matching(session)

    assert len(session.candidate_pairs) == 1
    assert session.candidate_pairs[0].distance is None


# ---------------------------------------------------------------------------
# AC-M4-13 — transitive NN matches produce separate pairs, not one cluster
# ---------------------------------------------------------------------------


def test_nn_transitive_abc_produces_two_separate_pairs_not_one_cluster():
    """AC-M4-13: A-B and B-C within threshold, A-C not within threshold ->
    exactly 2 CandidatePairs (A-B, B-C), each length 2 — no synthesized A-C
    pair, no 3-member cluster.

    "abc" vs "abcd" = edit distance 1 (within threshold 1)
    "abcd" vs "abcde" = edit distance 1 (within threshold 1)
    "abc" vs "abcde" = edit distance 2 (NOT within threshold 1)
    """
    csv_bytes = (
        b"StreetAddress,ZipCode,City\nabc,10001,NewYork\nabcd,10001,NewYork\nabcde,10001,NewYork\n"
    )
    mapping = ColumnMapping(street_col="StreetAddress", zip_col="ZipCode", city_col="City")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "levenshtein"
    session.algorithm_params = {"threshold": 1}

    run_matching(session)

    assert len(session.candidate_pairs) == 2
    pairs_as_sets = {tuple(pair.row_indices) for pair in session.candidate_pairs}
    assert pairs_as_sets == {(0, 1), (1, 2)}
    assert (0, 2) not in pairs_as_sets
    assert all(len(pair.row_indices) == 2 for pair in session.candidate_pairs)


# ---------------------------------------------------------------------------
# AC-M4-14 — NN pair distance is the single pairwise value, not a cluster max
# ---------------------------------------------------------------------------


def test_nn_pair_distance_is_the_single_pairwise_distance_not_a_max():
    """AC-M4-14: pair.distance equals the exact measured distance for that
    pair — not adjusted/maximized against any other pair. This is a
    deliberate reversal of M3's "cluster distance = max pairwise distance".

    "abc" vs "abcd" = edit distance 1
    "abcd" vs "abcde" = edit distance 1
    "abc" vs "abcde" = edit distance 2 (would have been the cluster max under M3)
    """
    csv_bytes = (
        b"StreetAddress,ZipCode,City\nabc,10001,NewYork\nabcd,10001,NewYork\nabcde,10001,NewYork\n"
    )
    mapping = ColumnMapping(street_col="StreetAddress", zip_col="ZipCode", city_col="City")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "levenshtein"
    session.algorithm_params = {"threshold": 2}

    run_matching(session)

    # All three pairwise combinations are within threshold=2.
    assert len(session.candidate_pairs) == 3
    distance_by_pair = {tuple(pair.row_indices): pair.distance for pair in session.candidate_pairs}
    assert distance_by_pair[(0, 1)] == 1.0
    assert distance_by_pair[(1, 2)] == 1.0
    assert distance_by_pair[(0, 2)] == 2.0
    # Critically, (0, 1)'s distance is NOT bumped up to the cluster max (2.0).


# ---------------------------------------------------------------------------
# AC-M4-15 — every CandidatePair.row_indices has exactly 2 elements
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "algorithm_key, algorithm_params",
    [
        ("fingerprint", {}),
        ("ngram_fingerprint", {"n": 2}),
        ("levenshtein", {"threshold": 3}),
        ("ncd", {"threshold": 5}),
    ],
)
def test_candidate_pair_row_indices_always_length_two(algorithm_key, algorithm_params):
    """AC-M4-15: regardless of algorithm, every CandidatePair has exactly 2
    row indices. Uses a 3-row mutually-similar fixture so each algorithm
    family produces at least one multi-row group to explode/pair."""
    csv_bytes = (
        b"StreetAddress,ZipCode,City\n"
        b"123 Main St,00501,Springfield\n"
        b"123 Main St.,00501,Springfield\n"
        b"123 main st,00501,Springfield\n"
    )
    mapping = ColumnMapping(street_col="StreetAddress", zip_col="ZipCode", city_col="City")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = algorithm_key
    session.algorithm_params = algorithm_params

    run_matching(session)

    assert all(len(pair.row_indices) == 2 for pair in session.candidate_pairs)


# ---------------------------------------------------------------------------
# AC-M4-16 — run_matching rebuilds candidate_pairs from scratch; no "checked"
# state is part of the domain model to begin with.
# ---------------------------------------------------------------------------


def test_run_matching_rebuilds_candidate_pairs_from_scratch_with_fresh_pair_ids():
    """AC-M4-16: a recompute fully replaces candidate_pairs with new pair_ids
    — no correlation attempted with a prior run's pairs."""
    csv_bytes = b"StreetAddress\n123 Main St\n123 MAIN ST.\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"

    # Pre-populate with a stale entry that should be wiped.
    session.candidate_pairs = [
        CandidatePair(pair_id="stale-id", row_indices=[99, 100], distance=None)
    ]

    run_matching(session)
    first_run_pair_ids = {pair.pair_id for pair in session.candidate_pairs}
    assert "stale-id" not in first_run_pair_ids
    assert all(pair.row_indices != [99, 100] for pair in session.candidate_pairs)

    run_matching(session)
    second_run_pair_ids = {pair.pair_id for pair in session.candidate_pairs}

    # Fresh pair_ids each run; no overlap with the previous run's ids.
    assert first_run_pair_ids.isdisjoint(second_run_pair_ids)


def test_itertools_combinations_sanity_check_for_four_member_cluster():
    """Hand-verifiable sanity check on the underlying explosion math: a
    4-member key-collision cluster yields C(4, 2) = 6 pairs, matching what
    itertools.combinations of [0, 1, 2, 3] produces."""
    expected_pairs = set(itertools.combinations(range(4), 2))
    assert len(expected_pairs) == 6

    csv_bytes = b"StreetAddress\n123 Main St\n123 MAIN ST.\n123 main st.\n123  MAIN  ST\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"

    run_matching(session)

    actual_pairs = {tuple(pair.row_indices) for pair in session.candidate_pairs}
    assert actual_pairs == expected_pairs
