# User Stories — Chore: OpenRefine-Style Frontend Redesign

Chore branch: `chore/frontend-redesign-openrefine`
Status: Written before the `coder` pass. Source: GitHub issue #10,
`docs/design/ui-design-spec.md` (synthesized this same BA pass from
`docs/design/reference/`).

This is a process/visual chore, not a numbered milestone — see `CLAUDE.md`'s
Workflow section, chore-loop variant. Scope is locked in as "visual only,
current structure": the existing 4-screen wizard (upload -> mapping ->
algorithm -> results) keeps its routes, forms, and field names; only colors,
typography, spacing, and component/layout CSS classes change.

---

## US-CHORE-1 — Recognize AddressRefine as a data-cleaning tool at a glance

**As a** user familiar with OpenRefine's interface conventions,
**I want** AddressRefine's header, forms, tables, and buttons to use a
similar visual language (palette, typography, control grouping),
**so that** the tool feels familiar and purpose-built for data cleaning
rather than a generic unstyled form app.

**Acceptance notes:**
- Applies to all 4 screens: `upload.html`, `mapping.html`, `algorithm.html`,
  `results.html`, plus the shared `base.html` shell.
- No functional behavior changes — same routes, same form fields, same
  validation rules as before this chore.
- Visual fidelity to the OpenRefine reference material is judged by the
  `tester` agent's Visual QA pass (Playwright screenshots vs.
  `docs/design/reference/screenshots/`), not asserted as a hard pass/fail
  in `pytest`.

---

## US-CHORE-2 — Scan a results table the way I would in OpenRefine

**As a** data steward reviewing candidate duplicate groups on the results
page,
**I want** the results table to have a shaded header row, alternating
zebra-striped body rows, and a visible hover highlight,
**so that** I can track rows visually across a wide table without losing my
place, the same way OpenRefine's clustering table behaves.

**Acceptance notes:**
- `.results-table` header row uses a distinct background shade from body
  rows (`--color-table-header-bg`).
- Body rows alternate between two background shades
  (`--color-table-row-odd` / `--color-table-row-even`).
- Hovering a row highlights it with a third, intermediate shade.
- No change to the table's columns, data, or the inert Accept/Reject
  buttons' functional state (still disabled placeholders pending M4).

---

## US-CHORE-3 — Fill in a multi-field form without it feeling like a long vertical list

**As a** user mapping CSV columns or choosing an algorithm and its
parameters,
**I want** related fields (e.g. the four mapping dropdowns, or an
algorithm's select + its parameter inputs) grouped and laid out
horizontally where there's room,
**so that** the form reads as a compact, organized control panel —
matching OpenRefine's "control-row" / "control-group" pattern — rather than
a long single-column stack.

**Acceptance notes:**
- `mapping.html`'s street/zip/city/country fields are wrapped in
  `.control-row` / `.control-group` containers per
  `docs/design/ui-design-spec.md`'s Layout pattern section.
- `algorithm.html`'s algorithm-select plus its conditional parameter
  field(s) (`n`, `threshold`) are similarly grouped.
- Every `name=`, `id=`, `required`, `min=`/`max=`/`step=` attribute and
  every POST target stays exactly as it was — only the wrapping markup and
  CSS classes change.
- The upload form (single file input + submit) is unaffected — it has only
  one logical control and doesn't need this pattern.

---

## US-CHORE-4 — Tell the primary action apart from a disabled one

**As a** user on any of the 4 screens,
**I want** the main submit button (Upload / Save mapping / Run matching) to
look clearly clickable, and the currently-inert Accept/Reject buttons on
the results page to look clearly disabled,
**so that** I don't waste a click on something that does nothing, and I
trust the primary action is the one to take.

**Acceptance notes:**
- Submit buttons use `.btn`/`.btn-primary` (flat-gray, bold-text per the
  reference's "Merge selected & re-cluster" treatment — not a saturated
  blue fill).
- The inert Accept/Reject buttons carry a visible `:disabled` treatment
  (reduced opacity, muted text) distinct from an enabled button.
- No JavaScript/HTMX wiring is added to these buttons in this chore — they
  remain non-functional placeholders until M4.

---

## US-CHORE-5 — Have requirements documentation a tester can actually check

**As the** orchestrating session preparing the `coder` pass for this chore,
**I want** a mix of objective, code-checkable requirements (specific CSS
custom properties, no inline styles, expected classes present) and clearly
labeled qualitative visual-fidelity criteria,
**so that** the `tester` agent has both a `pytest`-checkable bar and an
explicit, bounded Visual QA judgment call to make — not an all-subjective
"make it look nice" brief.

**Acceptance notes:**
- See `docs/ba/frd.md` FR-9.1 through FR-9.8 for the objective requirements.
- See FR-9.9 and `acceptance-criteria/chore-frontend-redesign.md`'s
  qualitative criteria section for the Visual QA judgment scope.
