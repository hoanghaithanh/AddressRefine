"""Core domain dataclasses shared across the app.

Kept intentionally minimal for Milestone 1 (upload + column mapping only).
Later milestones will extend `Session` with fields such as candidate pairs,
algorithm parameters, etc. — the dataclasses below are structured so that's
a additive change rather than a rewrite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ColumnMapping:
    """User-confirmed mapping of CSV headers to logical address fields."""

    street_col: str
    zip_col: str | None = None
    city_col: str | None = None
    country_col: str | None = None


@dataclass
class DatasetVersion:
    """A single immutable snapshot of the working dataset.

    `df` is intentionally typed as `Any` here (not `pandas.DataFrame`) so the
    domain model doesn't bind to a specific compute backend — mirrors the
    backend-agnostic `Any` typing used in `app.compute.backend.ComputeBackend`.
    """

    version: int
    df: Any
    created_from_merge: bool = False


@dataclass
class CandidatePair:
    """A group of row indices the matching algorithm believes are duplicates.

    `distance` is `None` for key-collision algorithms (Fingerprint, N-Gram
    Fingerprint) since they cluster by exact key equality rather than a
    pairwise distance score. Nearest-neighbor algorithms populate it with the
    maximum pairwise distance in the cluster.

    `pair_id` is a UUID4 string assigned by `matching_service` at construction
    time and is unique across all pairs in a single matching run.
    """

    pair_id: str
    row_indices: list[int]
    distance: float | None = None


@dataclass
class Session:
    """In-memory session state for a single user's working set.

    Only one dataset "thread" is tracked at a time (single session per the
    M1 spec). `versions` is a list so future milestones (merge) can append
    new `DatasetVersion`s without losing history.
    """

    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    versions: list[DatasetVersion] = field(default_factory=list)
    mapping: ColumnMapping | None = None
    original_filename: str | None = None
    algorithm_key: str | None = None
    algorithm_params: dict[str, Any] = field(default_factory=dict)
    candidate_pairs: list[CandidatePair] = field(default_factory=list)

    @property
    def current_df(self) -> Any:
        """Return the dataframe of the most recent dataset version, if any."""
        if not self.versions:
            return None
        return self.versions[-1].df
