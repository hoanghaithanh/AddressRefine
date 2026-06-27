"""Pandas-backed implementation of `ComputeBackend`."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

from app.compute.backend import ComputeBackend
from app.models.domain import ColumnMapping


class PandasComputeBackend(ComputeBackend):
    """`ComputeBackend` implementation using `pandas.DataFrame` as the frame type."""

    def load_csv(self, data: bytes) -> Any:
        # dtype=str + keep_default_na=False is deliberate: it preserves leading
        # zeros in zip codes (e.g. "00501") and prevents literal "NA" address
        # tokens from being coerced to NaN.
        frame = pd.read_csv(io.BytesIO(data), dtype=str, keep_default_na=False)
        if frame.shape[1] == 0 or frame.shape[0] == 0:
            raise ValueError("Uploaded CSV is empty or could not be parsed into any rows/columns.")
        return frame

    def get_headers(self, frame: Any) -> list[str]:
        return list(frame.columns)

    def extract_columns(self, frame: Any, mapping: ColumnMapping) -> dict[int, dict[str, str]]:
        result: dict[int, dict[str, str]] = {}
        for idx in frame.index:
            result[idx] = {
                "street": str(frame.at[idx, mapping.street_col]) if mapping.street_col else "",
                "zip": str(frame.at[idx, mapping.zip_col]) if mapping.zip_col else "",
                "city": str(frame.at[idx, mapping.city_col]) if mapping.city_col else "",
                "country": str(frame.at[idx, mapping.country_col]) if mapping.country_col else "",
            }
        return result

    def extract_street_addresses(self, frame: Any, mapping: ColumnMapping) -> dict[int, str]:
        if not mapping.street_col:
            return {idx: "" for idx in frame.index}
        return {idx: str(frame.at[idx, mapping.street_col]) for idx in frame.index}

    def replace_values(
        self, frame: Any, street_col: str, row_indices: list[int], new_value: str
    ) -> Any:
        raise NotImplementedError("implemented in a later milestone")

    def to_csv_bytes(self, frame: Any) -> bytes:
        return frame.to_csv(index=False).encode("utf-8")

    def row_count(self, frame: Any) -> int:
        return int(frame.shape[0])
