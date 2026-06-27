"""Compute backend factory.

Keeping a factory function (rather than importing `PandasComputeBackend`
directly everywhere) means a future Spark/Polars backend can be swapped in
behind `get_compute_backend()` without touching call sites.
"""

from __future__ import annotations

from app.compute.backend import ComputeBackend
from app.compute.pandas_backend import PandasComputeBackend


def get_compute_backend() -> ComputeBackend:
    """Return the active `ComputeBackend`. Always pandas-based for now."""
    return PandasComputeBackend()
