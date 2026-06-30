# Acceptance Criteria — Chore: OpenRefine-Style Frontend Redesign

Chore branch: `chore/frontend-redesign-openrefine`
Status: Written before the `coder` pass. Source: GitHub issue #10,
`docs/design/ui-design-spec.md`. Each AC is in Given/When/Then form except
where noted as qualitative. See `traceability-matrix.md` for the expected
test file/case mapping.

This chore is scoped as **visual only, current structure** — already
decided by the user (see issue #10 "Out of scope" and the BA brief for this
pass). The 4-screen wizard's routes, forms, field names, and validation are
unchanged. Anything from the OpenRefine reference material implying a
structural change (the editable "new cell value" field, the merge/export
action-bar footer, combining screens) is explicitly deferred to M4 and is
**not** an open question here — it is out of scope by design.

---

## Objective / code-checkable criteria

These map directly to `frd.md` FR-9.1 through FR-9.8 and are written to be
verified by a `pytest` test (CSS parsing, file content assertions, or
static grep) rather than by visual judgment.

### AC-CHORE-1 — Required CSS custom properties exist with specified values

**Given** `app/static/css/styles.css` after this chore,
**When** the `:root` block is parsed,
**Then** it defines at least the following custom properties with the
values from `docs/design/ui-design-spec.md`'s Palette table:
`--color-bg: #eeeeee`, `--color-surface: #ffffff`,
`--color-header-bg: #e3edfb`, `--color-header-border: #a9c6ee`,
`--color-text: #1f1f1f`, `--color-border: #cccccc`,
`--color-primary: #4a4a4a`, `--color-primary-hover: #333333`,
`--color-secondary-bg: #f4f4f4`, `--color-table-header-bg: #e0e0e0`,
`--color-table-row-odd: #eeeeee`, `--color-table-row-even: #ffffff`,
`--color-muted: #767676`, `--color-link: #1a4fa0`.

### AC-CHORE-2 — Required spacing custom properties exist

**Given** `app/static/css/styles.css` after this chore,
**Then** the `:root` block defines `--space-xs: 0.25rem`,
`--space-sm: 0.5rem`, `--space-md: 0.75rem`, `--space-lg: 1rem`,
`--space-xl: 1.5rem`.

### AC-CHORE-3 — No inline `style=` attributes in any shipped template

**Given** every `.html` file under `app/templates/` (including
`partials/`),
**When** each file's contents are scanned for a `style="` or `style='`
attribute,
**Then** no match is found in any file.

### AC-CHORE-4 — Header banner uses the new header colors

**Given** `app/templates/base.html`'s `.site-header` element and
`app/static/css/styles.css`'s `.site-header` rule,
**Then** the rule's `background` references `var(--color-header-bg)` and
its `border-bottom` references `var(--color-header-border)`.

### AC-CHORE-5 — Mapping form fields are grouped in `.control-row`/`.control-group`

**Given** `app/templates/mapping.html` after this chore,
**Then** the street/zip/city/country label+select pairs are each wrapped
in an element with class `control-group`, and those `control-group`
elements share a common parent with class `control-row`. The `name=`,
`id=`, and `required` attributes on each `<select>` are unchanged from
before this chore (statically diffable against the pre-chore file).

### AC-CHORE-6 — Algorithm form fields are grouped in `.control-row`/`.control-group`

**Given** `app/templates/algorithm.html` after this chore,
**Then** the algorithm `<select>` and its conditionally-rendered parameter
field(s) (`n`, `threshold`) are each wrapped in a `.control-group` element
sharing a common `.control-row` parent. All `name=`, `id=`, `min=`,
`max=`, `step=` attributes and the Jinja conditionals governing
`threshold` visibility are unchanged from before this chore.

### AC-CHORE-7 — Submit buttons carry `.btn` and `.btn-primary`

**Given** the rendered HTML of `upload.html` (Upload button),
`mapping.html` (Save mapping button), and `algorithm.html` (Run matching
button),
**Then** each submit `<button>` element's `class` attribute includes both
`btn` and `btn-primary`.

### AC-CHORE-8 — Results table has header shading, zebra rows, and hover styling defined

**Given** `app/static/css/styles.css`'s `.results-table` rule block after
this chore,
**Then** it defines: (a) a header-row rule (e.g. `.results-table thead` or
`.results-table th`) using `var(--color-table-header-bg)` as background;
(b) zebra-striping rules using `tr:nth-child(odd)` and `tr:nth-child(even)`
selectors referencing `var(--color-table-row-odd)` /
`var(--color-table-row-even)`; (c) a `tr:hover` rule with a background
distinct from both zebra shades.

### AC-CHORE-9 — Disabled Accept/Reject buttons carry a visible disabled treatment

**Given** `app/static/css/styles.css`'s button rules and
`app/templates/partials/_pair_row.html`'s Accept/Reject `<button
disabled>` elements,
**Then** a `:disabled` (or equivalent attribute-selector) CSS rule exists
that sets a reduced-opacity and/or muted-color treatment distinct from the
enabled `.btn-primary` appearance, and the Accept/Reject buttons carry the
`btn` class so that rule applies to them.

### AC-CHORE-10 — No functional/route regression

**Given** the full upload -> mapping -> algorithm -> results flow,
**When** the existing `pytest` suite (all tests from M1/M2/M3) is run
after this chore's CSS/template changes,
**Then** every existing test continues to pass unmodified — this chore
introduces zero functional/behavioral change to routers, services, or
algorithms.

---

## Qualitative / visual-fidelity criteria (judged by tester's Visual QA pass, not asserted as hard pass/fail)

These criteria describe the *intent* of the redesign in terms a human (or
the tester agent's screenshot-comparison judgment) can evaluate, but they
are not mechanically checkable the way AC-CHORE-1 through AC-CHORE-10 are.
Per `.claude/agents/tester.md`'s Visual QA pass, findings here are reported
as **Visual — Must fix** (wrong primary colors, missing components, badly
broken layout) or **Visual — Informational** (minor shade/spacing
differences, acceptable interpretation gaps where OpenRefine doesn't map
1:1 onto AddressRefine's screens) — never as a pytest pass/fail.

### AC-CHORE-11 (qualitative) — Overall palette reads as "OpenRefine-like"

The header banner's pale-blue tone, the flat neutral-gray buttons (rather
than a saturated blue), and the gray-bordered table should be
recognizable, side-by-side, as inspired by the reference screenshot
(`docs/design/reference/screenshots/AlgorithmSelectionAndResult.png`) —
not necessarily pixel-identical, since no raw design tokens were supplied
(see Open Questions below).

### AC-CHORE-12 (qualitative) — Density and typography feel comparable

Body text and table cells should read as comparably dense/compact to the
reference screenshot (smaller body font, bold-but-modest section
headings) rather than the larger, airier defaults AddressRefine used
before this chore.

### AC-CHORE-13 (qualitative) — Control-row layout reduces vertical sprawl on mapping/algorithm screens

The mapping and algorithm forms should visually read as a compact panel
of grouped controls (per the control-row/control-group pattern) rather
than a long one-field-per-line list, on a reasonably wide viewport (e.g.
1280px).

### AC-CHORE-14 (qualitative) — No screen looks "broken" or unstyled

None of the 4 screens should show unstyled raw browser-default form
controls, misaligned control-row wrapping, or a header banner that fails
to render its background color (a regression a screenshot would clearly
reveal even without OpenRefine in frame).

---

## Open Questions

### OQ-CHORE-1 — No raw design tokens supplied; spec colors are visual estimates

`docs/design/reference/design-tokens.md` is present but contains no actual
values ("Not yet populated"). All hex values in `docs/design/ui-design-spec.md`
(and therefore in AC-CHORE-1 above) were derived by visual estimation from
the single screenshot, not measured via browser DevTools. **Impact:** the
coder will implement exact hex values that are best-effort approximations,
not ground truth; the tester's Visual QA judgment (not byte-for-byte CSS
diffing) is the real fidelity gate. If pixel-accurate fidelity to
OpenRefine's actual computed styles matters to the user, `design-tokens.md`
should be populated from DevTools before/during the coder pass — otherwise
proceed with the estimated palette as specified.

### OQ-CHORE-2 — Single reference screenshot covers only the algorithm/results-like screen

Only one screenshot was provided
(`AlgorithmSelectionAndResult.png`, OpenRefine's clustering dialog), which
maps most directly onto `algorithm.html` + `results.html` combined.
`upload.html` (a plain file-input screen) and `mapping.html` (a column
dropdown form) have no directly analogous OpenRefine reference image, nor
does any error/flash-message state. The ui-design-spec extrapolates the
same palette/typography/control-row vocabulary to these screens as a
judgment call. **Impact:** the tester's Visual QA pass has no
screenshot to compare `upload.html` or `mapping.html` against pixel-for-
pixel and should judge those screens only against the *spec document*
(palette/typography/control-row description), flagging anything that
looks inconsistent with the algorithm/results screens' applied styling as
Informational rather than Must-fix, given the inherent extrapolation gap.
If the user later supplies more reference screenshots (e.g. an OpenRefine
project-creation/import screen for upload, or a faceted-browse screen for
mapping-like column selection), a follow-up BA pass should fold them in.

### OQ-CHORE-3 — No reference for hover/focus/disabled interaction states

The screenshot is a static capture; it cannot show a live `:hover` row, a
focused `<select>`, or a fully-disabled-button state. The ui-design-spec's
choices for these states (hover background shade, focus ring, disabled
opacity) are original design decisions consistent with the overall
palette, not directly observed in the reference material. **Impact:** the
tester's Visual QA pass cannot compare these specific states against a
reference image (there is nothing to compare them to) — it should instead
confirm they exist and look reasonable/consistent with the static states,
treating any complaint here as Informational at most.
