# User Stories — M3: Nearest-Neighbor Algorithms + Blocking

Milestone branch: `m3-nn-algorithms-blocking`
Status: Written before the `coder` pass. Source: GitHub issue #2, plan
section "Blocking" / "Algorithm interface" / "Milestones" item 3, and
the resolved open questions from the M3 BA pre-authoring pass.

---

## US-M3-1 — Run Levenshtein matching on my address dataset

**As a** data steward cleaning an address CSV,
**I want to** select "Levenshtein Distance" as the matching algorithm and
set an edit-distance threshold,
**so that** I can find address rows that are near-duplicates even when
they differ by a few characters (e.g. abbreviations, typos).

**Acceptance notes:**
- Threshold is a non-negative integer; default is 3.
- Matching only compares rows within the same block (zip prefix or city),
  so the run is fast even on larger CSVs.
- Results appear in the same candidate-group table used by M2's
  key-collision algorithms.

---

## US-M3-2 — Run NCD/PPM matching on my address dataset

**As a** data steward cleaning an address CSV,
**I want to** select "PPM / NCD" as the matching algorithm and set a
similarity threshold (displayed as an integer 1–10),
**so that** I can find address rows that share compressed-content
similarity even when token order or abbreviation style differs.

**Acceptance notes:**
- The displayed threshold (1–10) is scaled internally to 0.1–1.0; the
  user sees and sets the integer value.
- Threshold 0 and threshold > 10 are rejected with a clear error message.
- Results appear in the standard candidate-group table.

---

## US-M3-3 — Understand the similarity score shown for NN results

**As a** data steward reviewing candidate matches,
**I want to** see a distance or similarity score next to each candidate
group,
**so that** I can judge how confident I should be that the group
represents a real duplicate.

**Acceptance notes:**
- For Levenshtein results: the score shown is the maximum pairwise edit
  distance among all members of the group (integer).
- For NCD results: the score shown is the maximum pairwise NCD value
  among all members of the group (float, roughly 0–1).
- The column header reads "Distance" with a sub-label on the page
  identifying the scale ("edit distance" or "NCD score (0–1)") so the
  user is not left guessing what the number means.
- Key-collision algorithm results (M2 Fingerprint/N-Gram) continue to
  show "—" in this column — no regression.

---

## US-M3-4 — Match only addresses in the same geographic area

**As a** data steward with a large, geographically diverse CSV,
**I want** nearest-neighbor matching to restrict comparisons to rows
sharing the same zip-code prefix or city,
**so that** "123 Main St, Boston" is never spuriously compared to
"123 Main St, Houston" and I don't wait a long time for an O(n²) all-pairs run.

**Acceptance notes:**
- Block key = first 3 characters of the normalized (whitespace-stripped,
  lowercased) zip code, if zip is non-blank.
- Fallback: if zip is blank, block key = normalized city name, if
  city is non-blank.
- Rows with neither zip nor city go into a shared `"__unblocked__"` bucket
  and are compared only against each other (no cross-block comparison).
- Key-collision algorithms (Fingerprint, N-Gram Fingerprint) are
  unaffected by blocking — they ignore the `blocks` argument as before.

---

## US-M3-5 — Transitive near-duplicates merged into one group

**As a** data steamer reviewing results,
**I want** rows A, B, and C to appear as one group when A matches B and
B matches C (even if A and C don't directly exceed the threshold),
**so that** I can accept or reject the whole cluster at once without
hunting for hidden transitive connections.

**Acceptance notes:**
- Union-find is applied to all pairwise matches that fall within
  threshold; transitively connected pairs become one `CandidatePair`.
- The group's distance shows the maximum pairwise distance within the
  cluster (most conservative signal).

---

## US-M3-6 — Identify candidate groups across reruns

**As a** data steward who may rerun matching with different parameters,
**I want** each candidate group to have a stable unique ID,
**so that** future milestones (M4 accept/reject) can address individual
groups without ambiguity.

**Acceptance notes:**
- Each `CandidatePair` constructed by `matching_service` is assigned a
  `pair_id` (uuid4 string) at creation time.
- `pair_id` values are not required to be stable across reruns (a new
  run rebuilds all pairs from scratch); stability within a single run
  is sufficient.
