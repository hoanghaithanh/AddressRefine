# UAT Plan — Chore: OpenRefine-Style Frontend Redesign

Chore branch: `chore/frontend-redesign-openrefine`
Status: Written before the `coder` pass. Designed as a manual test script a
human (or the orchestrating session) can execute against a running
`uvicorn app.main:app --reload` instance after the `coder` and `tester`
passes complete. Steps map to `acceptance-criteria/chore-frontend-redesign.md`.

## Prerequisites

1. `pip install -r requirements-dev.txt` is up to date (includes
   `playwright`, per `CLAUDE.md` Setup).
2. `uvicorn app.main:app --reload` is running at `http://localhost:8000`.
3. A small CSV (any from prior milestones' UAT fixtures, e.g. `uat_m3.csv`,
   or a fresh hand-crafted one) is available to drive the flow through to
   a populated `/results` page.
4. Have `docs/design/reference/screenshots/AlgorithmSelectionAndResult.png`
   open side-by-side for visual comparison during Scenarios 3-4.

---

## Scenario 1 — Header banner styling

**Steps:**
1. Navigate to `http://localhost:8000/` (upload screen).

**Expected results:**
- The header banner ("AddressRefine" + step indicator) renders with a
  pale-blue background, distinct from the white page body below it.
- A visible border/rule separates the header from the page content.

**Pass criteria:** Header background is visibly blue-tinted, not white;
matches AC-CHORE-4.

---

## Scenario 2 — Upload screen button styling, no inline styles

**Steps:**
1. On the upload screen, inspect the "Upload" button visually and via
   browser DevTools (`Elements` panel).

**Expected results:**
- The button has a flat gray background with bold text — not a saturated
  blue fill.
- No element on the page has a `style="..."` attribute (check via
  DevTools "Inspect" on a few elements, or view source).

**Pass criteria:** Button looks like the spec's `.btn-primary` (flat gray,
bold), and `Ctrl+F` in view-source finds no `style="`.

---

## Scenario 3 — Mapping screen control-row layout

**Steps:**
1. Upload a CSV. On the mapping screen, observe the layout of the four
   field selectors (Street, Zip, City, Country) at a desktop viewport
   width (e.g. 1280px or wider).

**Expected results:**
- The four label+select pairs are arranged in a horizontal row (or wrap
  to a second row if the viewport is too narrow), not stacked one per
  line vertically as before this chore.
- Each field still behaves identically to before: required validation on
  Street, `-- choose --`/`-- none --` placeholders, best-guess
  pre-selection.

**Pass criteria:** Visually compact horizontal grouping; submitting with
a missing Street value still produces the same validation error as
before.

---

## Scenario 4 — Algorithm screen control-row layout + results table styling

**Steps:**
1. Confirm the mapping. On the algorithm screen, select each algorithm in
   turn (Fingerprint, N-Gram Fingerprint, Levenshtein, NCD) and observe
   the layout of the algorithm selector plus its conditional parameter
   field(s).
2. Submit with N-Gram Fingerprint (default `n=2`) to reach `/results`.
3. On the results page, compare the table's header row, zebra striping,
   and row-hover behavior against
   `docs/design/reference/screenshots/AlgorithmSelectionAndResult.png`.

**Expected results:**
- Algorithm select + parameter field(s) are visually grouped
  side-by-side (control-row pattern), not stacked vertically.
- The results table header row has a distinct gray shading from body
  rows.
- Body rows alternate between two shades (zebra striping).
- Hovering over a row highlights it with a third shade.
- The inert "Accept"/"Reject" buttons are visibly grayed-out/disabled,
  distinct from an active button.

**Pass criteria:** Table styling is recognizably similar in spirit to the
reference screenshot's clustering table (header shading + zebra rows);
disabled buttons look disabled; no functional regression (still cannot
click Accept/Reject — expected, M4 scope).

---

## Scenario 5 — No functional regression across the full flow

**Steps:**
1. Run the existing automated suite: `pytest -q` from the project root.
2. Manually repeat the M1-M3 UAT flows' happy paths (upload -> mapping ->
   algorithm -> results) for at least one key-collision algorithm
   (Fingerprint) and one nearest-neighbor algorithm (Levenshtein).

**Expected results:**
- `pytest -q` passes with the same test count as before this chore (no
  new failures, no skipped/xfail tests introduced by this chore).
- Both manual flows complete without HTTP 500s, with the same
  results/redirect behavior as documented in
  `uat/m2-fingerprint-algorithms.md` and `uat/m3-nn-algorithms-blocking.md`
  — only the visual presentation differs.

**Pass criteria:** Automated suite green; manual flows behave identically
to pre-chore UAT scenarios except for appearance.

---

## Scenario 6 — Playwright Visual QA pass (tester-executed, referenced here for completeness)

This scenario is executed by the `tester` agent as part of its Visual QA
pass (`.claude/agents/tester.md`), not by a human UAT runner, but is
recorded here so the chore's UAT plan accounts for it.

**Steps (performed by tester):**
1. Drive headless Chromium through all 4 screens via Playwright.
2. Capture a full-page screenshot per screen to `.playwright-output/`.
3. Compare each captured screenshot against
   `docs/design/reference/screenshots/AlgorithmSelectionAndResult.png`
   (for algorithm/results) and against the spec document's description
   (for upload/mapping, per OQ-CHORE-2 — no direct reference image
   exists for those two screens).

**Expected results:** Reported as **Visual — Must fix** /
**Visual — Informational** per the tester agent's report format.

**Pass criteria (for this chore's UAT exit):** No **Visual — Must fix**
findings outstanding before merge; Informational findings are
acknowledged but do not block.

---

## Exit criteria for this chore's UAT

All 6 scenarios pass: `pytest -q` green with no new failures, no inline
`style=` attributes found, header/button/table visual changes observable
per Scenarios 1-4, and the tester's Visual QA pass reports zero
outstanding **Visual — Must fix** findings.
