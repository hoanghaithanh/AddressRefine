"""Business-logic services layer.

Routers stay thin: they parse/validate input and delegate to modules here,
which mutate `Session` state and call into `app/algorithms/` and
`app/compute/`. No module here imports `pandas` directly — dataframe access
always goes through a `ComputeBackend` instance.
"""

from __future__ import annotations
