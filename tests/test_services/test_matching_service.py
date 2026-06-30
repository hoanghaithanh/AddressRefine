"""Tests for app/services/matching_service.py::run_matching."""

from __future__ import annotations

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


def test_run_matching_uses_extract_street_addresses(monkeypatch):
    """AC-M2-15: run_matching obtains addresses via the compute backend's
    extract_street_addresses, not by touching the frame directly."""
    csv_bytes = b"StreetAddress\n123 Main St\n123 MAIN ST.\n456 Oak Ave\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)

    calls: list[tuple] = []
    backend = PandasComputeBackend()
    original = backend.extract_street_addresses

    def _spy(frame, mapping_arg):
        calls.append((frame, mapping_arg))
        return original(frame, mapping_arg)

    monkeypatch.setattr(
        "app.services.matching_service.get_compute_backend",
        lambda: type("SpyBackend", (), {"extract_street_addresses": staticmethod(_spy)})(),
    )

    session.algorithm_key = "fingerprint"
    run_matching(session)

    assert len(calls) == 1
    assert calls[0][1] is mapping


def test_run_matching_rebuilds_candidate_pairs_from_scratch():
    """AC-M2-16: a previous run's candidate_pairs are fully replaced, not appended to."""
    csv_bytes = b"StreetAddress\n123 Main St\n123 MAIN ST.\n456 Oak Ave\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"

    # Pre-populate candidate_pairs with a stale entry that should be wiped.
    session.candidate_pairs = [
        CandidatePair(pair_id="stale-id", row_indices=[99, 100], distance=None)
    ]

    run_matching(session)

    assert len(session.candidate_pairs) == 1
    assert session.candidate_pairs[0].row_indices == [0, 1]
    assert all(pair.row_indices != [99, 100] for pair in session.candidate_pairs)


def test_run_matching_called_twice_does_not_duplicate_entries():
    csv_bytes = b"StreetAddress\n123 Main St\n123 MAIN ST.\n456 Oak Ave\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"

    run_matching(session)
    first_run_pairs = list(session.candidate_pairs)
    run_matching(session)

    assert len(session.candidate_pairs) == len(first_run_pairs)


def test_cluster_of_three_explodes_into_three_pairwise_entries():
    """AC-M4-11 (supersedes M2's AC-M2-17): a 3-row cluster explodes into
    exactly 3 pairwise CandidatePair entries (one per combination), each with
    row_indices of length 2 — not one 3-member entry, per M4's pairwise-only
    CandidatePair model."""
    csv_bytes = b"StreetAddress\n123 Main St\n123 MAIN ST.\n123 main st.\n456 Oak Ave\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"

    run_matching(session)

    assert len(session.candidate_pairs) == 3
    pairs_as_sets = {tuple(pair.row_indices) for pair in session.candidate_pairs}
    assert pairs_as_sets == {(0, 1), (0, 2), (1, 2)}
    assert all(len(pair.row_indices) == 2 for pair in session.candidate_pairs)


def test_singleton_keys_produce_no_candidate_pair():
    """AC-M2-10 (service-level): rows with no matching key produce zero entries."""
    csv_bytes = b"StreetAddress\n123 Main St\n456 Oak Ave\n789 Pine Rd\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"

    run_matching(session)

    assert session.candidate_pairs == []


def test_run_matching_distance_is_none_for_key_collision_algorithm():
    csv_bytes = b"StreetAddress\n123 Main St\n123 MAIN ST.\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"

    run_matching(session)

    assert len(session.candidate_pairs) == 1
    assert session.candidate_pairs[0].distance is None


def test_run_matching_raises_without_mapping():
    session = Session(session_id="test-session")
    backend = PandasComputeBackend()
    frame = backend.load_csv(b"StreetAddress\n123 Main St\n")
    session.versions.append(DatasetVersion(version=1, df=frame))
    session.algorithm_key = "fingerprint"

    with pytest.raises(ValueError):
        run_matching(session)


def test_run_matching_raises_without_dataset():
    session = Session(session_id="test-session")
    session.mapping = ColumnMapping(street_col="StreetAddress")
    session.algorithm_key = "fingerprint"

    with pytest.raises(ValueError):
        run_matching(session)


def test_run_matching_raises_without_algorithm_key():
    csv_bytes = b"StreetAddress\n123 Main St\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)

    with pytest.raises(ValueError):
        run_matching(session)


def test_run_matching_raises_for_unknown_algorithm_key():
    csv_bytes = b"StreetAddress\n123 Main St\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "not_a_real_algorithm"

    with pytest.raises(ValueError):
        run_matching(session)


def test_run_matching_with_ngram_algorithm_uses_algorithm_params():
    csv_bytes = b"StreetAddress\nab-cab\nABCAB\nzzzzz\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "ngram_fingerprint"
    session.algorithm_params = {"n": 2}

    run_matching(session)

    assert len(session.candidate_pairs) == 1
    assert session.candidate_pairs[0].row_indices == [0, 1]


def test_run_matching_rebuilds_candidate_pairs_pairwise_count_matches_combinations():
    """AC-M4-15 sanity check at the matching_service level: a 4-row cluster
    explodes into C(4, 2) = 6 pairwise entries."""
    csv_bytes = b"StreetAddress\n123 Main St\n123 MAIN ST.\n123 main st.\n123  MAIN  ST\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"

    run_matching(session)

    assert len(session.candidate_pairs) == 6
    assert all(len(pair.row_indices) == 2 for pair in session.candidate_pairs)
