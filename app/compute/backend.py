"""Abstract compute backend interface.

`Any` is used for the frame type throughout (never `pandas.DataFrame`) so
this interface stays agnostic of the underlying dataframe library — a future
milestone may add a Spark-backed implementation behind the same interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.domain import ColumnMapping


class ComputeBackend(ABC):
    """Operations the rest of the app needs performed on a tabular dataset."""

    @abstractmethod
    def load_csv(self, data: bytes) -> Any:
        """Parse raw CSV bytes into a backend-specific frame."""
        raise NotImplementedError

    @abstractmethod
    def get_headers(self, frame: Any) -> list[str]:
        """Return the column headers of `frame`, in order."""
        raise NotImplementedError

    @abstractmethod
    def extract_columns(self, frame: Any, mapping: ColumnMapping) -> dict[int, dict[str, str]]:
        """Return {row_index: {"street": ..., "zip": ..., "city": ..., "country": ...}}.

        Missing/unmapped columns or NaN values are represented as "".
        """
        raise NotImplementedError

    @abstractmethod
    def extract_street_addresses(self, frame: Any, mapping: ColumnMapping) -> dict[int, str]:
        """Return {row_index: street_address_string}."""
        raise NotImplementedError

    @abstractmethod
    def replace_values(
        self, frame: Any, street_col: str, row_indices: list[int], new_value: str
    ) -> Any:
        """Replace `street_col` values at `row_indices` with `new_value`.

        Used by the merge feature (later milestone).
        """
        raise NotImplementedError

    @abstractmethod
    def to_csv_bytes(self, frame: Any) -> bytes:
        """Serialize `frame` back to CSV bytes."""
        raise NotImplementedError

    @abstractmethod
    def row_count(self, frame: Any) -> int:
        """Return the number of rows in `frame`."""
        raise NotImplementedError
