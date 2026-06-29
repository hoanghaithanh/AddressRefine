"""Matching algorithms package.

Every module under this package must stay backend-agnostic: algorithms
operate on plain `dict[int, str]` address maps (and similar plain dicts),
never on a `pandas.DataFrame`. See `app/compute/backend.py` and
`CLAUDE.md`'s "compute/ vs algorithms/" section for the rationale.
"""

from __future__ import annotations
