"""Tests for app/services/merge_service.py::apply_merge.

Covers AC-M4-25 through AC-M4-31 from
`docs/ba/acceptance-criteria/m4-merge-review.md`.
"""

from __future__ import annotations

import pytest

from app.compute.pandas_backend import PandasComputeBackend
from app.models.domain import CandidatePair, ColumnMapping, DatasetVersion, Session
from app.services.merge_service import MergeConflictError, MergeRequestRow, apply_merge


def _make_session_with_pairs(csv_bytes: bytes, mapping: ColumnMapping) -> Session:
    """Build a session with a loaded dataset, an algorithm selection, and an
    empty candidate_pairs list the test populates manually (so tests don't
    depend on a specific algorithm's matching behavior)."""
    backend = PandasComputeBackend()
    frame = backend.load_csv(csv_bytes)
    session = Session(session_id="test-session")
    session.versions.append(DatasetVersion(version=1, df=frame))
    session.mapping = mapping
    session.algorithm_key = "fingerprint"
    session.algorithm_params = {}
    return session


def _street_values(session: Session, street_col: str) -> dict[int, str]:
    backend = PandasComputeBackend()
    extracted = backend.extract_street_addresses(session.current_df, session.mapping)
    return extracted


# ---------------------------------------------------------------------------
# AC-M4-25 — checked pair's both rows rewritten to "New cell value"
# ---------------------------------------------------------------------------


def test_apply_merge_rewrites_both_rows_in_checked_pair_to_new_value():
    csv_bytes = b"StreetAddress\n123 Main St\n123 Main Street\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session_with_pairs(csv_bytes, mapping)
    session.candidate_pairs = [CandidatePair(pair_id="pair-1", row_indices=[0, 1], distance=None)]
    backend = PandasComputeBackend()

    apply_merge(session, backend, [MergeRequestRow(pair_id="pair-1", new_value="X")])

    values = _street_values(session, "StreetAddress")
    assert values[0] == "X"
    assert values[1] == "X"


# ---------------------------------------------------------------------------
# AC-M4-26 — merge is idempotent when one side already equals the target value
# ---------------------------------------------------------------------------


def test_apply_merge_is_idempotent_when_one_side_already_equals_new_value():
    csv_bytes = b"StreetAddress\nX\n123 Main Street\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session_with_pairs(csv_bytes, mapping)
    session.candidate_pairs = [CandidatePair(pair_id="pair-1", row_indices=[0, 1], distance=None)]
    backend = PandasComputeBackend()

    apply_merge(session, backend, [MergeRequestRow(pair_id="pair-1", new_value="X")])

    values = _street_values(session, "StreetAddress")
    assert values[0] == "X"
    assert values[1] == "X"


# ---------------------------------------------------------------------------
# AC-M4-27 — conflicting checked rows targeting the same row block the merge
# ---------------------------------------------------------------------------


def test_apply_merge_blocks_on_conflicting_targets_for_same_row():
    """Pair A-B wants row A -> "B"; pair A-C wants row A -> "C". Both target
    row A's index (0) with disagreeing values."""
    csv_bytes = b"StreetAddress\nA\nB\nC\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session_with_pairs(csv_bytes, mapping)
    session.candidate_pairs = [
        CandidatePair(pair_id="pair-ab", row_indices=[0, 1], distance=None),
        CandidatePair(pair_id="pair-ac", row_indices=[0, 2], distance=None),
    ]
    backend = PandasComputeBackend()

    with pytest.raises(MergeConflictError) as exc_info:
        apply_merge(
            session,
            backend,
            [
                MergeRequestRow(pair_id="pair-ab", new_value="B"),
                MergeRequestRow(pair_id="pair-ac", new_value="C"),
            ],
        )

    assert exc_info.value.conflicts == {0: ["B", "C"]}


def test_apply_merge_conflict_error_lists_conflicting_row_and_values():
    """The conflict error carries the conflicting row index and the sorted
    list of disagreeing target values."""
    csv_bytes = b"StreetAddress\nA\nB\nC\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session_with_pairs(csv_bytes, mapping)
    session.candidate_pairs = [
        CandidatePair(pair_id="pair-ab", row_indices=[0, 1], distance=None),
        CandidatePair(pair_id="pair-ac", row_indices=[0, 2], distance=None),
    ]
    backend = PandasComputeBackend()

    with pytest.raises(MergeConflictError) as exc_info:
        apply_merge(
            session,
            backend,
            [
                MergeRequestRow(pair_id="pair-ab", new_value="ZZZ"),
                MergeRequestRow(pair_id="pair-ac", new_value="AAA"),
            ],
        )

    assert 0 in exc_info.value.conflicts
    assert set(exc_info.value.conflicts[0]) == {"ZZZ", "AAA"}


# ---------------------------------------------------------------------------
# AC-M4-28 — a blocked (conflicting) merge mutates nothing
# ---------------------------------------------------------------------------


def test_apply_merge_blocked_merge_mutates_nothing():
    csv_bytes = b"StreetAddress\nA\nB\nC\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session_with_pairs(csv_bytes, mapping)
    session.candidate_pairs = [
        CandidatePair(pair_id="pair-ab", row_indices=[0, 1], distance=None),
        CandidatePair(pair_id="pair-ac", row_indices=[0, 2], distance=None),
    ]
    backend = PandasComputeBackend()

    versions_before = list(session.versions)
    pairs_before = list(session.candidate_pairs)
    df_before = session.current_df

    with pytest.raises(MergeConflictError):
        apply_merge(
            session,
            backend,
            [
                MergeRequestRow(pair_id="pair-ab", new_value="B"),
                MergeRequestRow(pair_id="pair-ac", new_value="C"),
            ],
        )

    assert session.versions == versions_before
    assert session.candidate_pairs == pairs_before
    assert session.current_df is df_before


def test_apply_merge_blocked_merge_does_not_call_replace_values():
    """AC-M4-27: a blocked merge never calls ComputeBackend.replace_values at all."""
    csv_bytes = b"StreetAddress\nA\nB\nC\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session_with_pairs(csv_bytes, mapping)
    session.candidate_pairs = [
        CandidatePair(pair_id="pair-ab", row_indices=[0, 1], distance=None),
        CandidatePair(pair_id="pair-ac", row_indices=[0, 2], distance=None),
    ]

    calls = []

    class _SpyBackend(PandasComputeBackend):
        def replace_values(self, frame, street_col, row_indices, new_value):
            calls.append((street_col, list(row_indices), new_value))
            return super().replace_values(frame, street_col, row_indices, new_value)

    backend = _SpyBackend()

    with pytest.raises(MergeConflictError):
        apply_merge(
            session,
            backend,
            [
                MergeRequestRow(pair_id="pair-ab", new_value="B"),
                MergeRequestRow(pair_id="pair-ac", new_value="C"),
            ],
        )

    assert calls == []


# ---------------------------------------------------------------------------
# AC-M4-29 — successful merge appends a new DatasetVersion(created_from_merge=True)
# ---------------------------------------------------------------------------


def test_apply_merge_appends_new_dataset_version_with_created_from_merge_true():
    csv_bytes = b"StreetAddress\n123 Main St\n123 Main Street\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session_with_pairs(csv_bytes, mapping)
    session.candidate_pairs = [CandidatePair(pair_id="pair-1", row_indices=[0, 1], distance=None)]
    backend = PandasComputeBackend()
    previous_version = session.versions[-1]

    apply_merge(session, backend, [MergeRequestRow(pair_id="pair-1", new_value="X")])

    assert len(session.versions) == 2
    new_version = session.versions[-1]
    assert new_version.version == previous_version.version + 1
    assert new_version.created_from_merge is True


# ---------------------------------------------------------------------------
# AC-M4-30 — successful merge reruns matching with currently-selected algorithm/params
# ---------------------------------------------------------------------------


def test_apply_merge_reruns_matching_with_currently_selected_algorithm_and_params(
    monkeypatch,
):
    csv_bytes = b"StreetAddress\n123 Main St\n123 Main Street\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session_with_pairs(csv_bytes, mapping)
    session.algorithm_key = "levenshtein"
    session.algorithm_params = {"threshold": 5}
    session.candidate_pairs = [CandidatePair(pair_id="pair-1", row_indices=[0, 1], distance=1.0)]
    backend = PandasComputeBackend()

    calls = []
    import app.services.merge_service as merge_svc

    def _spy_run_matching(sess):
        calls.append((sess.algorithm_key, dict(sess.algorithm_params)))

    monkeypatch.setattr(merge_svc, "run_matching", _spy_run_matching)

    apply_merge(session, backend, [MergeRequestRow(pair_id="pair-1", new_value="X")])

    assert calls == [("levenshtein", {"threshold": 5})]


def test_apply_merge_actually_reruns_matching_end_to_end():
    """Without mocking run_matching: after a successful merge that makes two
    rows identical, a fresh fingerprint run finds them as a duplicate pair."""
    csv_bytes = b"StreetAddress\n123 Main St\n456 Oak Ave\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session_with_pairs(csv_bytes, mapping)
    session.algorithm_key = "fingerprint"
    session.algorithm_params = {}
    session.candidate_pairs = [CandidatePair(pair_id="pair-1", row_indices=[0, 1], distance=None)]
    backend = PandasComputeBackend()

    apply_merge(session, backend, [MergeRequestRow(pair_id="pair-1", new_value="123 Main St")])

    # Both rows now read "123 Main St" -> fingerprint algorithm should find
    # them as a duplicate pair on the rerun.
    assert len(session.candidate_pairs) == 1
    assert session.candidate_pairs[0].row_indices == [0, 1]


# ---------------------------------------------------------------------------
# AC-M4-31 — zero checked rows is a no-op
# ---------------------------------------------------------------------------


def test_apply_merge_zero_checked_rows_is_noop_no_version_appended():
    csv_bytes = b"StreetAddress\n123 Main St\n123 Main Street\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session_with_pairs(csv_bytes, mapping)
    session.candidate_pairs = [CandidatePair(pair_id="pair-1", row_indices=[0, 1], distance=None)]
    backend = PandasComputeBackend()

    versions_before = list(session.versions)
    pairs_before = list(session.candidate_pairs)

    # Should not raise.
    apply_merge(session, backend, [])

    assert session.versions == versions_before
    assert session.candidate_pairs == pairs_before


def test_apply_merge_zero_checked_rows_does_not_invoke_run_matching(monkeypatch):
    csv_bytes = b"StreetAddress\n123 Main St\n123 Main Street\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session_with_pairs(csv_bytes, mapping)
    session.candidate_pairs = [CandidatePair(pair_id="pair-1", row_indices=[0, 1], distance=None)]
    backend = PandasComputeBackend()

    calls = []
    import app.services.merge_service as merge_svc

    monkeypatch.setattr(merge_svc, "run_matching", lambda sess: calls.append(sess))

    apply_merge(session, backend, [])

    assert calls == []


# ---------------------------------------------------------------------------
# Stale pair_id handling — not directly an AC, but exercised by the
# documented "silently skip" behavior in merge_service's docstring/comment.
# ---------------------------------------------------------------------------


def test_apply_merge_stale_pair_id_is_skipped_not_an_error():
    csv_bytes = b"StreetAddress\n123 Main St\n123 Main Street\n"
    mapping = ColumnMapping(street_col="StreetAddress")
    session = _make_session_with_pairs(csv_bytes, mapping)
    session.candidate_pairs = [CandidatePair(pair_id="pair-1", row_indices=[0, 1], distance=None)]
    backend = PandasComputeBackend()

    # pair_id "stale" doesn't exist in candidate_pairs; should be a no-op,
    # not an exception.
    apply_merge(session, backend, [MergeRequestRow(pair_id="stale", new_value="X")])

    assert len(session.versions) == 1
