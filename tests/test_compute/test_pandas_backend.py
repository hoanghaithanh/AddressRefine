"""Tests for `PandasComputeBackend` (app/compute/pandas_backend.py)."""

from __future__ import annotations

import pytest

from app.compute.pandas_backend import PandasComputeBackend
from app.models.domain import ColumnMapping
from tests.conftest import sample_csv_bytes


@pytest.fixture
def backend() -> PandasComputeBackend:
    return PandasComputeBackend()


def test_load_csv_valid_returns_correct_row_count_and_headers(backend):
    frame = backend.load_csv(sample_csv_bytes())

    assert backend.row_count(frame) == 2
    assert backend.get_headers(frame) == ["ZipCode", "StreetAddress", "City", "Country"]


def test_load_csv_empty_bytes_raises_value_error(backend):
    with pytest.raises(ValueError):
        backend.load_csv(b"")


def test_load_csv_header_only_raises_value_error(backend):
    """A CSV with a header row but zero data rows has shape[0] == 0."""
    with pytest.raises(ValueError):
        backend.load_csv(b"ZipCode,StreetAddress,City,Country\n")


def test_extract_columns_preserves_leading_zero_zip(backend):
    frame = backend.load_csv(sample_csv_bytes())
    mapping = ColumnMapping(
        street_col="StreetAddress", zip_col="ZipCode", city_col="City", country_col="Country"
    )

    extracted = backend.extract_columns(frame, mapping)

    assert extracted[0]["zip"] == "00501"


def test_extract_columns_preserves_literal_na_string(backend):
    frame = backend.load_csv(sample_csv_bytes())
    mapping = ColumnMapping(
        street_col="StreetAddress", zip_col="ZipCode", city_col="City", country_col="Country"
    )

    extracted = backend.extract_columns(frame, mapping)

    # Row index 1 has ZipCode == "NA" in the sample data.
    assert extracted[1]["zip"] == "NA"


def test_extract_columns_unmapped_logical_column_is_empty_string(backend):
    frame = backend.load_csv(sample_csv_bytes())
    mapping = ColumnMapping(
        street_col="StreetAddress", zip_col=None, city_col=None, country_col=None
    )

    extracted = backend.extract_columns(frame, mapping)

    assert extracted[0]["zip"] == ""
    assert extracted[0]["city"] == ""
    assert extracted[0]["country"] == ""
    assert extracted[0]["street"] == "123 Main St"


def test_replace_values_sets_street_col_at_given_indices(backend):
    """AC-M4-35/36: replace_values sets street_col to new_value at every given
    row index, and other rows/columns are unaffected. Supersedes M1's
    test_replace_values_raises_not_implemented now that M4 implements this
    for real."""
    frame = backend.load_csv(sample_csv_bytes())

    updated = backend.replace_values(frame, "StreetAddress", [0], "123 Merged St")

    mapping = ColumnMapping(
        street_col="StreetAddress", zip_col="ZipCode", city_col="City", country_col="Country"
    )
    extracted = backend.extract_columns(updated, mapping)
    assert extracted[0]["street"] == "123 Merged St"
    # Row 1 (untouched) and other columns of row 0 are unaffected.
    assert extracted[1]["street"] == "456 Oak Ave"
    assert extracted[0]["zip"] == "00501"


def test_replace_values_multiple_row_indices(backend):
    """AC-M4-35: replace_values accepts multiple row indices in one call."""
    frame = backend.load_csv(sample_csv_bytes())

    updated = backend.replace_values(frame, "StreetAddress", [0, 1], "999 Unified Ave")

    mapping = ColumnMapping(street_col="StreetAddress")
    extracted = backend.extract_columns(updated, mapping)
    assert extracted[0]["street"] == "999 Unified Ave"
    assert extracted[1]["street"] == "999 Unified Ave"


def test_replace_values_does_not_raise_not_implemented(backend):
    """AC-M4-36: replace_values no longer raises NotImplementedError."""
    frame = backend.load_csv(sample_csv_bytes())

    try:
        backend.replace_values(frame, "StreetAddress", [0], "new value")
    except NotImplementedError:
        pytest.fail("replace_values must not raise NotImplementedError as of M4")
