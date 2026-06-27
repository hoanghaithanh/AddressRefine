"""Pydantic request/response schemas (distinct from the dataclass domain models)."""

from __future__ import annotations

from pydantic import BaseModel, model_validator


class MappingForm(BaseModel):
    """POST body for the column-mapping form.

    `street_col` is always required. At least one of `zip_col`/`city_col`
    must also be supplied, since street-only matching is not useful for the
    fuzzy-matching milestones that build on this mapping.
    """

    street_col: str
    zip_col: str | None = None
    city_col: str | None = None
    country_col: str | None = None

    @model_validator(mode="after")
    def require_zip_or_city(self) -> MappingForm:
        if not self.zip_col and not self.city_col:
            raise ValueError("At least one of zip_col or city_col is required.")
        return self
