"""Merge orchestration: rewrites checked pairs' street values and reruns matching.

`apply_merge` is the only mutating action reachable from the combined
algorithm/results page (`POST /merge`) — there is no per-pair accept/reject
model as of M4 (see `CLAUDE.md`/`docs/ba/frd.md` FR-6).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.compute.backend import ComputeBackend
from app.models.domain import CandidatePair, DatasetVersion, Session
from app.services.matching_service import run_matching


@dataclass
class MergeRequestRow:
    """One checked row submitted from the results table.

    `pair_id` correlates this row back to the `CandidatePair` it came from;
    `new_value` is the row's current "New cell value" text at submit time.
    Unchecked rows are never represented here — their absence from the
    submitted list of `MergeRequestRow`s *is* the "not checked" signal.
    """

    pair_id: str
    new_value: str


class MergeConflictError(Exception):
    """Raised when two or more checked rows disagree on a shared row's target value.

    `conflicts` maps a conflicting row index to the sorted list of distinct
    target values different checked rows tried to assign it.
    """

    def __init__(self, conflicts: dict[int, list[str]]) -> None:
        self.conflicts = conflicts
        rows_desc = "; ".join(
            f"row {row_index}: {values!r}" for row_index, values in sorted(conflicts.items())
        )
        super().__init__(f"Merge blocked by conflicting target values ({rows_desc}).")


def apply_merge(
    session: Session, backend: ComputeBackend, merge_requests: list[MergeRequestRow]
) -> None:
    """Rewrite checked pairs' rows to their target value and rerun matching.

    Builds a `row_index -> target_value` map from `merge_requests` (matched
    against `session.candidate_pairs` by `pair_id`). If any underlying row
    index is targeted by more than one distinct value, raises
    `MergeConflictError` without mutating `session` at all. Otherwise, groups
    row indices by target value, calls `backend.replace_values` once per
    distinct value (chaining the returned frame through each call), appends a
    new `DatasetVersion(version=len(session.versions) + 1, created_from_merge=True)`,
    and reruns `run_matching(session)` using the session's current (unchanged)
    `algorithm_key`/`algorithm_params`.

    Zero checked rows (`merge_requests == []`) is a no-op: no exception, no
    new version, no rerun, `session.candidate_pairs` unchanged.
    """
    if not merge_requests:
        return

    pairs_by_id: dict[str, CandidatePair] = {pair.pair_id: pair for pair in session.candidate_pairs}

    target_by_row: dict[int, str] = {}
    conflicts: dict[int, set[str]] = {}

    for request_row in merge_requests:
        pair = pairs_by_id.get(request_row.pair_id)
        if pair is None:
            # Stale pair_id (e.g. table was recomputed between render and
            # submit) — silently skip rather than mutating unrelated rows.
            continue
        for row_index in pair.row_indices:
            existing = target_by_row.get(row_index)
            if existing is None:
                target_by_row[row_index] = request_row.new_value
            elif existing != request_row.new_value:
                conflicts.setdefault(row_index, {existing}).add(request_row.new_value)

    if conflicts:
        raise MergeConflictError(
            {row_index: sorted(values) for row_index, values in conflicts.items()}
        )

    if not target_by_row:
        # All submitted pair_ids were stale; nothing to do.
        return

    rows_by_target: dict[str, list[int]] = {}
    for row_index, target_value in target_by_row.items():
        rows_by_target.setdefault(target_value, []).append(row_index)

    frame = session.current_df
    street_col = session.mapping.street_col

    for target_value, row_indices in rows_by_target.items():
        frame = backend.replace_values(frame, street_col, row_indices, target_value)

    session.versions.append(
        DatasetVersion(version=len(session.versions) + 1, df=frame, created_from_merge=True)
    )

    run_matching(session)
