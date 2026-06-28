# User Stories — M2: Fingerprint + N-Gram Fingerprint Algorithms + Read-Only Results

Status: Forward-looking, written before the `coder` pass starts. Source:
GitHub issue #1 ("M2: Fingerprint + N-Gram Fingerprint algorithms +
read-only results view") and the plan's Milestone 2 section.

## US-M2-1: See candidate duplicate addresses grouped automatically

As a user who has mapped my CSV's columns, I want the app to group rows
that likely describe the same address using a fast, parameter-light
algorithm, so that I get an initial view of likely duplicates without
manually comparing rows.

- Related: `FingerprintAlgorithm` (`app/algorithms/fingerprint.py`),
  `matching_service.run_matching`.

## US-M2-2: Tune grouping sensitivity via N-Gram Fingerprint

As a user whose addresses have typos or minor token reordering that plain
Fingerprint's token-based key misses, I want an N-Gram-based alternative
algorithm (with an adjustable n-gram size), so that I can catch matches
that whole-token clustering would miss.

- Related: `NGramFingerprintAlgorithm` (`app/algorithms/fingerprint.py`),
  `ParamSpec` for `n` (default `2`).

## US-M2-3: Choose which algorithm to run

As a user, I want a page where I can pick Fingerprint or N-Gram
Fingerprint and (for N-Gram) set its `n` parameter, so that I control how
matching is performed before I commit to reviewing results.

- Related: `GET/POST /algorithm` (`app/routers/algorithm.py`).

## US-M2-4: See the results of running the chosen algorithm

As a user, I want a results page listing the candidate groups the chosen
algorithm produced, so that I can see what it found before any
accept/reject functionality exists.

- Related: `GET /results` (`app/routers/results.py`). Per the GitHub
  issue, accept/reject controls may be present in the markup but must be
  inert in M2 (no working mutation endpoint yet — that's M4).

## US-M2-5: Trust that algorithm code won't be tied to pandas internals

As the project maintainer, I want `app/algorithms/` to only ever consume
plain `dict[int, str]` and never a DataFrame, so that a future Spark
backend can be added without rewriting matching logic.

- Related: `MatchingAlgorithm` ABC (`app/algorithms/base.py`),
  `ComputeBackend.extract_street_addresses`.

## US-M2-6: Move straight from mapping into algorithm selection

As a user who has just confirmed my column mapping, I want to land on the
algorithm-selection page next, not back on the mapping page, so that the
upload -> mapping -> algorithm -> results flow reads as one continuous
sequence instead of a dead end at mapping.

- Related: `POST /mapping` (`app/routers/mapping.py`) redirect target
  changes from `/mapping` to `/algorithm` as part of M2 (see AC-M2-24;
  resolves OQ-M2-1).

## US-M2-7: Be told clearly when no duplicates were found

As a user whose chosen algorithm/parameters found no candidate
duplicates, I want the results page to tell me that plainly and suggest
what to try next (a different algorithm, or different parameters), so
that I'm not left staring at a blank page wondering if something is
broken.

- Related: `GET /results` empty-state rendering (see AC-M2-26; resolves
  OQ-M2-3).
