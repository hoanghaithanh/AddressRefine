"""Matching algorithm interface shared by all `app/algorithms/` implementations.

This module (and every other module under `app/algorithms/`) must never
import `pandas` or otherwise touch a DataFrame: algorithms only ever see
plain `dict[int, str]` address maps handed to them by
`app/services/matching_service.py`, which itself obtains them via
`ComputeBackend.extract_street_addresses`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AlgorithmFamily(StrEnum):
    """Broad category of matching algorithm.

    `KEY_COLLISION` algorithms (Fingerprint, N-Gram Fingerprint — M2) group
    rows by exact equality of a derived key. `NEAREST_NEIGHBOR` algorithms
    (Levenshtein, PPM/NCD — M3) instead score pairwise distance.
    """

    KEY_COLLISION = "key_collision"
    NEAREST_NEIGHBOR = "nearest_neighbor"


@dataclass
class ParamSpec:
    """Describes one configurable parameter of a `MatchingAlgorithm`.

    Used to render a parameter input on the algorithm-selection form and to
    supply a default value when the user doesn't override it.
    """

    name: str
    label: str
    param_type: type
    default: Any


@dataclass
class AlgorithmOutput:
    """Result of running a `MatchingAlgorithm`.

    `clusters` is populated by key-collision algorithms: a mapping from a
    derived key to the list of row indices sharing that key. `pairs` is
    reserved for nearest-neighbor algorithms (later milestones) and is
    `None`/empty for key-collision algorithms.
    """

    clusters: dict[str, list[int]] = field(default_factory=dict)
    pairs: list[tuple[int, int, float]] | None = None


class MatchingAlgorithm(ABC):
    """Common interface every matching algorithm implements.

    Subclasses declare `key`/`label`/`family` as class variables and
    optionally override `param_specs` if they expose configurable
    parameters (e.g. N-Gram Fingerprint's `n`).
    """

    key: str
    label: str
    family: AlgorithmFamily
    param_specs: list[ParamSpec] = []

    @abstractmethod
    def run(
        self,
        addresses: dict[int, str],
        blocks: dict[str, list[int]] | None,
        params: dict[str, Any],
    ) -> AlgorithmOutput:
        """Run this algorithm over `addresses` and return its result.

        `addresses` maps row index to the raw (unnormalized) street address
        string for that row. `blocks` optionally restricts comparisons to
        rows sharing the same block key (used by nearest-neighbor algorithms
        in later milestones; key-collision algorithms ignore it). `params`
        carries user-supplied parameter overrides, keyed by `ParamSpec.name`.
        """
        raise NotImplementedError
