"""Tests for app/services/matching_service.py — M3 nearest-neighbor path.

Covers AC-M3-24 through AC-M3-29 (NN path, union-find, pair_id, distance).
"""

from __future__ import annotations

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
# AC-M3-24 — run_matching calls extract_columns for NN algorithms
# ---------------------------------------------------------------------------


def test_run_matching_nn_calls_extract_columns(monkeypatch):
    """AC-M3-24: for NN algorithms, run_matching calls backend.extract_columns
    (not just extract_street_addresses) to obtain zip/city for blocking."""
    csv_bytes = (
        b"StreetAddress,ZipCode,City\n"
        b"123 Main St,00501,Springfield\n"
        b"123 Main Street,00501,Springfield\n"
    )
    mapping = ColumnMapping(street_col="StreetAddress", zip_col="ZipCode", city_col="City")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "levenshtein"
    session.algorithm_params = {"threshold": 10}

    extract_columns_calls: list = []
    backend = PandasComputeBackend()
    original_extract_columns = backend.extract_columns
    original_extract_street = backend.extract_street_addresses

    def spy_extract_columns(frame, mapping_arg):
        extract_columns_calls.append(mapping_arg)
        return original_extract_columns(frame, mapping_arg)

    def spy_extract_street(frame, mapping_arg):
        return original_extract_street(frame, mapping_arg)

    class _SpyBackend:
        extract_columns = staticmethod(spy_extract_columns)
        extract_street_addresses = staticmethod(spy_extract_street)

    monkeypatch.setattr(
        "app.services.matching_service.get_compute_backend",
        lambda: _SpyBackend(),
    )

    run_matching(session)

    assert len(extract_columns_calls) >= 1
    assert extract_columns_calls[0] is mapping


# ---------------------------------------------------------------------------
# AC-M3-25 — run_matching passes blocks=None for key-collision algorithms
# ---------------------------------------------------------------------------


def test_run_matching_key_collision_passes_none_blocks(monkeypatch):
    """AC-M3-25: fingerprint algorithm receives blocks=None — no compute_blocks call."""
    csv_bytes = b"StreetAddress\n123 Main St\n123 MAIN ST.\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"

    compute_blocks_calls: list = []

    import app.services.matching_service as svc

    original_compute_blocks = svc.compute_blocks

    def spy_compute_blocks(rows):
        compute_blocks_calls.append(rows)
        return original_compute_blocks(rows)

    monkeypatch.setattr(svc, "compute_blocks", spy_compute_blocks)

    run_matching(session)

    # compute_blocks must NOT have been called for a key-collision algorithm.
    assert compute_blocks_calls == []


# ---------------------------------------------------------------------------
# AC-M3-26 — union-find produces one CandidatePair per transitive cluster
# ---------------------------------------------------------------------------


def test_run_matching_union_find_merges_transitive_pairs():
    """AC-M3-26: A-B and B-C within threshold → one CandidatePair with all three rows."""
    # "abc", "abcd", "abcde": edit distances 1 and 1, all within threshold=2
    csv_bytes = (
        b"StreetAddress,ZipCode,City\n"
        b"abc,10001,NewYork\n"
        b"abcd,10001,NewYork\n"
        b"abcde,10001,NewYork\n"
        b"zzzzzzzzzzzzzzz,10001,NewYork\n"  # completely different, shouldn't match
    )
    mapping = ColumnMapping(street_col="StreetAddress", zip_col="ZipCode", city_col="City")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "levenshtein"
    session.algorithm_params = {"threshold": 2}

    run_matching(session)

    # All three rows (0, 1, 2) should be in the same CandidatePair.
    matching_pairs = [p for p in session.candidate_pairs if 0 in p.row_indices]
    assert len(matching_pairs) == 1
    assert set(matching_pairs[0].row_indices) == {0, 1, 2}


# ---------------------------------------------------------------------------
# AC-M3-27 — CandidatePair.distance is the maximum pairwise distance
# ---------------------------------------------------------------------------


def test_run_matching_distance_is_max_pairwise_in_cluster():
    """AC-M3-27: CandidatePair.distance equals the max pairwise distance in the cluster.

    "abc" vs "abcd" = edit distance 1
    "abcd" vs "abcde" = edit distance 1
    "abc" vs "abcde" = edit distance 2

    The max pairwise distance is 2.
    """
    csv_bytes = (
        b"StreetAddress,ZipCode,City\nabc,10001,NewYork\nabcd,10001,NewYork\nabcde,10001,NewYork\n"
    )
    mapping = ColumnMapping(street_col="StreetAddress", zip_col="ZipCode", city_col="City")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "levenshtein"
    session.algorithm_params = {"threshold": 2}

    run_matching(session)

    assert len(session.candidate_pairs) == 1
    pair = session.candidate_pairs[0]
    # The maximum edit distance in the cluster is 2 (between "abc" and "abcde").
    assert pair.distance == 2.0


# ---------------------------------------------------------------------------
# AC-M3-28 — each CandidatePair has a unique pair_id (uuid4 string)
# ---------------------------------------------------------------------------


def test_run_matching_nn_assigns_unique_pair_ids():
    """AC-M3-28: every CandidatePair from a NN run has a non-empty, unique pair_id."""
    # Two separate clusters: 0-1 in zip 10001, 2-3 in zip 20002
    csv_bytes = (
        b"StreetAddress,ZipCode,City\n"
        b"abc,10001,CityA\n"
        b"abcd,10001,CityA\n"
        b"xyz,20002,CityB\n"
        b"xyzw,20002,CityB\n"
    )
    mapping = ColumnMapping(street_col="StreetAddress", zip_col="ZipCode", city_col="City")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "levenshtein"
    session.algorithm_params = {"threshold": 2}

    run_matching(session)

    assert len(session.candidate_pairs) >= 1
    pair_ids = [p.pair_id for p in session.candidate_pairs]
    assert all(isinstance(pid, str) and pid != "" for pid in pair_ids)
    # All pair_ids are unique.
    assert len(set(pair_ids)) == len(pair_ids)


def test_run_matching_key_collision_assigns_unique_pair_ids():
    """AC-M3-28: CandidatePairs from key-collision runs also get unique pair_ids."""
    csv_bytes = b"StreetAddress\n123 Main St\n123 MAIN ST.\n456 Oak Ave\n456 OAK AVE\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"

    run_matching(session)

    pair_ids = [p.pair_id for p in session.candidate_pairs]
    assert all(isinstance(pid, str) and pid != "" for pid in pair_ids)
    assert len(set(pair_ids)) == len(pair_ids)


# ---------------------------------------------------------------------------
# AC-M3-29 — run_matching rebuilds candidate_pairs from scratch (NN path)
# ---------------------------------------------------------------------------


def test_run_matching_nn_rebuilds_candidate_pairs_from_scratch():
    """AC-M3-29: stale candidate_pairs from a previous NN run are fully replaced."""
    csv_bytes = b"StreetAddress,ZipCode,City\nabc,10001,CityA\nabcd,10001,CityA\n"
    mapping = ColumnMapping(street_col="StreetAddress", zip_col="ZipCode", city_col="City")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "levenshtein"
    session.algorithm_params = {"threshold": 2}

    # Pre-populate with stale data.
    session.candidate_pairs = [
        CandidatePair(pair_id="stale-id", row_indices=[99, 100], distance=999.0)
    ]

    run_matching(session)

    # No stale entry should survive.
    assert all(p.row_indices != [99, 100] for p in session.candidate_pairs)
    assert all(p.pair_id != "stale-id" for p in session.candidate_pairs)


def test_run_matching_nn_produces_fresh_pair_ids_on_repeated_calls():
    """AC-M3-29: calling run_matching twice replaces pair_ids entirely (no duplicates
    from first run persist into second run)."""
    csv_bytes = b"StreetAddress,ZipCode,City\nabc,10001,CityA\nabcd,10001,CityA\n"
    mapping = ColumnMapping(street_col="StreetAddress", zip_col="ZipCode", city_col="City")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "levenshtein"
    session.algorithm_params = {"threshold": 2}

    run_matching(session)
    first_pair_ids = {p.pair_id for p in session.candidate_pairs}

    run_matching(session)
    second_pair_ids = {p.pair_id for p in session.candidate_pairs}

    # Second run generates new uuid4 pair_ids; they should differ from the first run's ids.
    # (uuid4 collision probability is negligible.)
    assert first_pair_ids != second_pair_ids


# ---------------------------------------------------------------------------
# AC-M3-30 — CandidatePair has pair_id field
# ---------------------------------------------------------------------------


def test_candidate_pair_has_pair_id_field():
    """AC-M3-30: CandidatePair dataclass exposes a pair_id: str field."""
    pair = CandidatePair(pair_id="test-uuid", row_indices=[0, 1], distance=2.0)

    assert hasattr(pair, "pair_id")
    assert pair.pair_id == "test-uuid"
    assert isinstance(pair.pair_id, str)


def test_candidate_pair_distance_field_still_present():
    """AC-M3-30: pair_id is added without removing the existing distance field."""
    pair = CandidatePair(pair_id="pid", row_indices=[0, 1], distance=3.5)

    assert pair.distance == 3.5

    pair_no_dist = CandidatePair(pair_id="pid2", row_indices=[0, 1])
    assert pair_no_dist.distance is None


# ---------------------------------------------------------------------------
# __unblocked__ rows are included in NN matching
# ---------------------------------------------------------------------------


def test_run_matching_nn_unblocked_rows_are_matched():
    """AC-M3-4 / AC-M3-24: rows in the __unblocked__ bucket are still compared
    pairwise within that bucket."""
    # No zip or city → both rows go to __unblocked__
    csv_bytes = b"StreetAddress,ZipCode,City\nabc,,\nabcd,,\n"
    mapping = ColumnMapping(street_col="StreetAddress", zip_col="ZipCode", city_col="City")
    session = _make_session(csv_bytes, mapping)
    session.algorithm_key = "levenshtein"
    session.algorithm_params = {"threshold": 2}

    run_matching(session)

    assert len(session.candidate_pairs) == 1
    assert set(session.candidate_pairs[0].row_indices) == {0, 1}
