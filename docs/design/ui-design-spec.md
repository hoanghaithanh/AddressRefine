# UI Design Spec — OpenRefine Visual Language for AddressRefine

Status: Authored during the `business-analyst` pass for the `chore/frontend-redesign-openrefine`
chore (GitHub issue #10). Synthesizes `docs/design/reference/screenshots/AlgorithmSelectionAndResult.png`
and `docs/design/reference/html-snippets/element.html` into a concrete, code-applicable spec.

## Scope boundary (already decided — see issue #10 and CLAUDE.md)

This spec covers **visual restyling only** of AddressRefine's existing 4-screen wizard
(upload -> mapping -> algorithm -> results). It does **not** change template structure,
does **not** merge screens, and does **not** introduce the editable "new cell value" field
or the merge/export action-bar footer that appear in the OpenRefine reference dialog —
those are functional pieces of M4 (review/accept/representative-value/merge) and will be
built then, reusing the palette/typography/component classes defined here. Anywhere the
reference material's structure doesn't map onto AddressRefine's current screens, this spec
simply does not apply that part of the reference (no open question — already resolved by
the user's scope decision).

## Source material consulted

- `docs/design/reference/screenshots/AlgorithmSelectionAndResult.png` — OpenRefine's
  "Cluster and edit column" dialog. This is the only screenshot provided; it shows
  OpenRefine's algorithm-control-row, results table, and dialog header/footer chrome.
  Read directly via the `Read` tool (renders as an image).
- `docs/design/reference/html-snippets/element.html` — captured DOM for the same dialog.
  No CSS rules or inline color values are present in this file (the long lines are
  encoded `href` query strings for "Browse this cluster" links, not stylesheets) — it is
  useful only for confirming real OpenRefine class names and structural nesting
  (`dialog-frame`, `dialog-header`, `dialog-body`, `clustering-dialog-control-row`,
  `clustering-dialog-control-group`, `clustering-dialog-table-container`,
  `clustering-dialog-entry-table`, alternating `tr.odd`/`tr.even` rows, `tr.header`).
- `docs/design/reference/design-tokens.md` — present but **empty** ("Not yet populated").
  No raw computed-style values (hex codes, font stacks, px values) were supplied. All
  colour/typography/spacing values below are visually estimated from the screenshot, not
  read from a computed-style export. See Open Questions in the BA report for the
  consequence of this gap.
- `app/static/css/styles.css` and `app/templates/base.html` — read for current state, to
  express this spec as deltas (old token/value -> new value) rather than abstractly.

## Palette

OpenRefine's "Cluster and edit column" dialog uses a light, low-saturation palette: a
pale blue header banner, white dialog body, light-gray table header and odd-row zebra
stripe, white even-row stripe, and a muted gray border/divider color throughout. Buttons
are flat gray with a slightly darker "primary" emphasis (the bold "Merge selected &
re-cluster" button) rather than a saturated brand blue.

| Custom property | Current value | New value | Replaces / notes |
|---|---|---|---|
| `--color-bg` | `#f7f7fa` | `#eeeeee` | Page background; OpenRefine's overall canvas behind the white dialog/content reads as a slightly darker neutral gray than the current near-white. |
| `--color-surface` | *(new)* | `#ffffff` | New token: white card/panel background, used by `.content`-level containers, forms, tables. Factors out the repeated bare `#ffffff` literals in the current stylesheet. |
| `--color-header-bg` | *(new)* | `#e3edfb` | New token: pale blue banner background, matching the screenshot's dialog-header strip ("Cluster and edit column..."). Applied to `.site-header` in place of plain white. |
| `--color-header-border` | *(new)* | `#a9c6ee` | New token: the slightly more saturated blue rule under the header banner visible in the screenshot. |
| `--color-text` | `#1f2430` | `#1f1f1f` | Body text; OpenRefine uses a near-black, slightly warmer dark gray rather than a navy-tinted dark. |
| `--color-border` | `#d8dce3` | `#cccccc` | General hairline border color used by tables, forms, cards — OpenRefine's borders read as a flat mid-gray, not a cool blue-gray. |
| `--color-primary` | `#2f6fed` | `#4a4a4a` | Primary button background. OpenRefine does not use a saturated brand blue for buttons in this dialog — its "emphasized" button (`Merge selected & re-cluster`) is bold-text dark gray on light gray, not a colored button. Replaces the blue primary button with a neutral dark-gray "primary" treatment; see Buttons section for the bold-vs-regular distinction this implies. |
| `--color-primary-text` | `#ffffff` | `#ffffff` | Unchanged — text on dark buttons stays white. |
| `--color-primary-hover` | *(new)* | `#333333` | New token: hover state for primary buttons (darken on hover, matching the `button:hover` opacity pattern already in place, expressed as a real color this time). |
| `--color-secondary-bg` | *(new)* | `#f4f4f4` | New token: flat light-gray background for secondary buttons (`Select all`, `Deselect all`, `Close` in the reference footer) — distinguishes secondary actions from the emphasized primary action. |
| `--color-table-header-bg` | *(new)* | `#e0e0e0` | New token: table header row (`tr.header`) background — a medium-light gray, distinctly darker than the zebra stripes. |
| `--color-table-row-odd` | *(new)* | `#eeeeee` | New token: odd-row zebra background (`tr.odd` in the reference markup). |
| `--color-table-row-even` | *(new)* | `#ffffff` | New token: even-row background (`tr.even`), i.e. plain white — alternates with the odd-row gray. |
| `--color-error-bg` | `#fdecea` | `#fdecea` | Unchanged — no error state shown in the reference material (see Open Questions). |
| `--color-error-text` | `#9b1c1c` | `#9b1c1c` | Unchanged, same reason. |
| `--color-muted` | `#6b7280` | `#767676` | Secondary/muted text (step-future nav items, helper copy) — OpenRefine's muted gray is flatter/warmer than the current cool gray. |
| `--color-link` | *(new)* | `#1a4fa0` | New token: hyperlink color, matching the visible blue "Find out more…" link style in the reference description text. Used by any in-content `<a>` (e.g. the results-page link back to the Algorithm step). |

Notes:
- The pale-blue header banner (`--color-header-bg`) and its border are the single most
  visually distinctive, confidently-observed element from the screenshot — apply it to
  `.site-header` in `base.html`'s shared shell, which is the closest AddressRefine
  equivalent of OpenRefine's `dialog-header`.
- Exact hex values above are visual estimates (eyedropper-equivalent judgment from the
  screenshot), not lab-measured or extracted via DevTools. Treat them as a faithful
  starting point; the tester's Visual QA pass (Playwright screenshot vs. reference image)
  is the actual fidelity gate, not byte-equality of hex codes.

## Typography

OpenRefine's dialog uses a plain sans-serif system stack at a small, dense body size, with
a noticeably larger, bold dialog title.

| Element | Current | New | Notes |
|---|---|---|---|
| Base font stack | `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` | unchanged | Already matches OpenRefine's plain-OS-sans approach; no reference evidence to justify a different stack (e.g. no custom webfont visible in the screenshot). |
| Base body size | implicit browser default (no `font-size` set on `body`) | `14px` (`0.875rem` against a `16px` root) | OpenRefine's table/body text reads noticeably smaller/denser than typical default 16px body copy. Set explicitly on `body` in `styles.css`. |
| `.site-header h1` | `1.25rem` | `1.05rem`, `font-weight: 600` | De-emphasize the app title slightly relative to the new bolder dialog-style heading treatment below, so the header banner reads closer to OpenRefine's title bar proportions. |
| Page/section heading (`h2`, e.g. "Choose a matching algorithm") | browser default `h2` sizing | `1.15rem`, `font-weight: 700` | Matches the bold, ~18-20px-equivalent "Cluster and edit column..." dialog title weight/size relationship to body text shown in the screenshot (title is bold and roughly 1.3-1.5x body size, not browser-default `h2` scale which is much larger). |
| Table header cells (`.results-table th`) | inherits body size/weight | `0.85rem`, `font-weight: 700`, slightly letter-spaced | OpenRefine's table header row text is bold, same-or-smaller size than body cells, all-caps is *not* used (preserve sentence case, e.g. "Distance", "Actions"). |
| Helper/description copy (e.g. upload/mapping/algorithm intro `<p>`) | inherits body | `0.9rem`, `color: var(--color-muted)` | Matches the smaller, gray descriptive paragraph under the OpenRefine dialog title. |

## Spacing scale

Introduce a small explicit scale (as custom properties) rather than continuing with ad hoc
rem values scattered through the stylesheet:

| Token | Value | Usage |
|---|---|---|
| `--space-xs` | `0.25rem` | tight gaps (e.g. label-to-sublabel) |
| `--space-sm` | `0.5rem` | control-group internal gaps, button padding (vertical) |
| `--space-md` | `0.75rem` | form field stacking gap (replaces the current bare `0.75rem` in `form { gap: ... }`) |
| `--space-lg` | `1rem` | control-row gap between control-groups, card padding (replaces ad hoc `1.25rem`/`1rem` mix) |
| `--space-xl` | `1.5rem` | page-level margins (`.content` padding/margin) |

## Layout pattern: control-row / control-group

The single most portable structural pattern from the reference markup (confirmed in
`element.html` lines 8-39) is OpenRefine's two-level grouping for form controls laid out
horizontally:

```html
<div class="clustering-dialog-control-row">      <!-- horizontal flex row -->
  <div class="clustering-dialog-control-group">  <!-- one labeled control, vertical label+input -->
    <label>Method</label>
    <select>...</select>
  </div>
  <div class="clustering-dialog-control-group">
    <label>Distance function</label>
    <select>...</select>
  </div>
  <!-- ...more groups... -->
  <div class="control-group" style="text-align:right">367 clusters included from 383 total</div>
</div>
```

This maps directly onto AddressRefine's **mapping form** (street/zip/city/country selects,
currently stacked vertically one per line) and **algorithm form** (algorithm select +
n-gram-size/threshold params, currently also stacked vertically). Adopt equivalent classes:

- `.control-row` — flex container, `display: flex; flex-wrap: wrap; gap: var(--space-lg); align-items: flex-end;` — groups related controls on one visual row instead of one-per-line.
- `.control-group` — `display: flex; flex-direction: column; gap: var(--space-xs);` — a single label+input pair, the unit that `.control-row` arranges horizontally.

Applying this to AddressRefine: the mapping form's four selects become one `.control-row`
containing four `.control-group`s (label above select, as already structured per-field —
just regrouped horizontally instead of vertically). The algorithm form's algorithm-select +
conditional n/threshold params become one `.control-row` with up to two `.control-group`s
(mirroring how the reference shows the method selector and its dependent param fields
side by side in the same row). The upload form (single file input + submit button) has
only one logical control and does not need this pattern — it stays as-is structurally.

This is a CSS/markup-class change only — the underlying Jinja form fields, `name=`
attributes, validation, and POST targets in `mapping.html`/`algorithm.html` are unchanged;
only the wrapping `<div>` structure and CSS classes around the existing `<label>`/`<select>`
pairs change, which is squarely "visual restyling," not a structural redesign.

## Table styling

Reference: `clustering-dialog-entry-table` in `element.html` + the visible table in the
screenshot.

- **Header row** (`tr.header` / `.results-table th`): background `var(--color-table-header-bg)`,
  bold text, bottom border `1px solid var(--color-border)`, no vertical cell borders.
- **Body rows**: zebra striping using `var(--color-table-row-odd)` / `var(--color-table-row-even)`
  alternating by row position (`tr:nth-child(odd)` / `tr:nth-child(even)` — CSS-only, no
  template change needed since Jinja already emits rows in a `{% for %}` loop in document
  order).
- **Row hover**: add a hover state not present in the current stylesheet —
  `background: #e8e8e8` (a shade between the two zebra tones) on `tr:hover` within
  `.results-table tbody`, giving a visible "which row am I pointing at" affordance the
  reference's dense table benefits from, even though the screenshot is a static capture
  and can't show a live hover state (see Open Questions).
- **Borders**: outer table border `1px solid var(--color-border)`, consistent with the
  current `.results-table` rule; no internal vertical rules (matches the reference's
  horizontal-only rule style).
- **Cell padding**: keep the current `0.6rem 0.9rem` — already close to the reference's
  dense-but-legible cell padding; no change needed here.

This applies directly to `app/static/css/styles.css`'s existing `.results-table` rule
block and to `partials/_results_table.html` / `partials/_pair_row.html` (class names only,
no new columns/fields — M2/M3's existing `<th>`/`<td>` structure is preserved).

## Button styling

Reference: the dialog footer shows a clear primary/secondary distinction — `Select all`,
`Deselect all`, `Export clusters`, `Close` are flat light-gray buttons with regular-weight
text; `Merge selected & re-cluster` is the same flat light-gray shape but with **bold**
text, marking it as the primary/default action without resorting to a saturated accent
color.

| Variant | Background | Text | Border | Font-weight | Usage in AddressRefine |
|---|---|---|---|---|---|
| `.btn` (base) | `var(--color-secondary-bg)` | `var(--color-text)` | `1px solid var(--color-border)` | `400` | Base class all buttons share (border-radius `3px`, padding `var(--space-sm) var(--space-lg)`). |
| `.btn-primary` | `var(--color-secondary-bg)` (same flat gray — not a colored fill) | `var(--color-text)` | `1px solid var(--color-border)` | `700` (bold) | Main submit button per screen: "Upload", "Save mapping", "Run matching". Replaces the current saturated-blue `button` default. |
| `.btn-secondary` | `var(--color-secondary-bg)` | `var(--color-text)` | `1px solid var(--color-border)` | `400` | Not yet used by any *currently wired* control (no secondary actions exist pre-M4), but the class is defined now so M4's "Accept"/"Reject" buttons (currently `disabled` placeholders in `_pair_row.html`) can adopt it without another restyling pass. |
| `.btn:hover` / `.btn-primary:hover` | `var(--color-primary-hover)` background, white text | — | — | — | Hover state — darkens rather than the current `opacity: 0.9` trick, closer to OpenRefine's solid-darken hover feedback. |
| `.btn:disabled` | `var(--color-secondary-bg)` at reduced opacity (`0.5`) | `var(--color-muted)` | `1px solid var(--color-border)` | `400` | Applies to the inert Accept/Reject buttons already present in `_pair_row.html` — gives them a visseparable disabled look instead of full default button styling that implies clickability. |

Note the deliberate move away from a saturated blue "primary" button to a flat-gray,
bold-vs-regular distinction — this is the single biggest behavioral change this spec asks
of `styles.css`'s existing `button` rule, and is called out explicitly here in case it
reads as a regression in perceived "branding" rather than an intentional OpenRefine-fidelity
choice.

## Component inventory and interaction states

| Component | Current selector(s) | New/renamed class(es) | States covered |
|---|---|---|---|
| Header banner | `.site-header`, `.site-header h1` | same names, new colors per Palette | static only (no interactive state) |
| Step indicator | `.stepper`, `.step`, `.step.current`, `.step-future` | unchanged names, restyled colors (`.step.current` uses `--color-text` + bold instead of `--color-primary` blue, since primary is no longer a blue accent) | current vs. future vs. completed-but-not-current (existing three states, no new state added) |
| Flash banner | `.flash`, `.flash-error`, `.flash-info` | unchanged names; colors unchanged (no reference evidence for an error/info banner — see Open Questions) | error, info (existing two; no new state) |
| Form shell | bare `form` selector | `.form-panel` (explicit class, applied in each `<form>` tag) on `--color-surface` background | static |
| Control row/group | n/a (new) | `.control-row`, `.control-group` | static (layout-only; no interaction state) |
| Select/input | bare `select`, `input[type="file"]` | `.field` (shared class for all text/select/file/number inputs) | default, `:focus` (new — add a visible `box-shadow`/border-color change on focus, since none exists today and OpenRefine's native-control style implies visible focus rings), `:disabled` (new, for the hidden-threshold edge case in `algorithm.html`) |
| Buttons | bare `button` | `.btn`, `.btn-primary`, `.btn-secondary` | default, `:hover`, `:disabled` (see Button styling table above) |
| Results table | `.results-table` | unchanged name, restyled | header row, zebra body rows, `:hover` row (new state), empty state (`.results-empty-state`, unchanged) |
| Pair row | `.pair-row-addresses`, `.pair-row-index` | unchanged names, restyled colors only | static (Accept/Reject buttons inside follow the Button styling above, including `:disabled`) |

## Explicit reference -> AddressRefine screen mapping

| Reference element (screenshot / `element.html`) | AddressRefine screen/component it informs |
|---|---|
| `dialog-header` pale-blue banner + bold title | `base.html`'s `.site-header` (shared across all 4 screens) |
| Descriptive gray paragraph under the title ("Find groups of different cell values...") | The existing intro `<p>` on each screen (`upload.html`, `mapping.html`, `algorithm.html`) — typography only (smaller, muted) |
| `clustering-dialog-control-row` / `clustering-dialog-control-group` (Method / Distance function / Radius selectors) | `mapping.html`'s four-field form and `algorithm.html`'s algorithm-select + param fields — re-laid-out horizontally via `.control-row`/`.control-group` |
| `control-group` "367 clusters included from 383 total" (right-aligned summary text) | No direct current equivalent; informs a *future* (not-this-chore) summary line on `results.html`, noted only for awareness — not implemented now since it's not a CSS-only change to an existing element. |
| `clustering-dialog-entry-table` (header row, `tr.odd`/`tr.even` zebra rows) | `partials/_results_table.html` + `.results-table` CSS — header shading, zebra striping, row hover |
| Per-row checkboxes + "Values in cluster" list | `partials/_pair_row.html`'s existing `.pair-row-addresses` list — visual styling of the `<ul>`/`<li>` only; the reference's *functional* checkboxes (select-which-value-to-keep) are out of scope, reserved for M4 |
| "New cell value" editable text input per row | Explicitly **out of scope for this chore** — reserved for M4 (representative-value selection) |
| Dialog footer (`Select all` / `Deselect all` / `Export clusters` / `Merge selected & re-cluster` / `Close`) | Explicitly **out of scope for this chore** — reserved for M4 (merge action bar); informs the future `.btn`/`.btn-primary` choice already specified above so M4 can reuse it without restyling |
| Flat gray buttons, bold-vs-regular primary/secondary distinction | All 4 screens' submit buttons (`upload.html` "Upload", `mapping.html` "Save mapping", `algorithm.html` "Run matching") via `.btn-primary` |

## Out of scope for this chore (reserved for M4)

Per the locked-in scope decision in issue #10:

- The editable "New cell value" text input per cluster row.
- The "Merge?" per-row selection checkbox and per-value "use this value" sub-checkboxes.
- The dialog-style action-bar footer (`Select all`, `Deselect all`, `Export clusters`,
  `Merge selected & re-cluster`, `Close`).
- Any structural change to combine upload/mapping/algorithm/results into a single
  screen/dialog.

These are noted here only so the M4 BA pass can find this spec's palette/button/table
tokens ready to reuse, not as something this chore implements.

## Open Questions

See the BA pass report for the ranked list delivered to the orchestrating session. Summary
of the two raised here for completeness:

1. **No raw design tokens were provided** (`design-tokens.md` is empty) — all hex/px
   values in this spec are visual estimates from a single screenshot, not measured values.
   If pixel-perfect fidelity to OpenRefine's actual computed styles matters, someone should
   populate `design-tokens.md` from DevTools before/during the coder pass; otherwise the
   tester's Visual QA judgment call is the de facto fidelity bar.
2. **Only one reference screenshot was provided**, covering OpenRefine's clustering dialog
   (closest analog to `algorithm.html` + `results.html` combined). No reference exists for
   AddressRefine's `upload.html` (a plain file-input screen) or `mapping.html` (a column
   dropdown form) as distinct OpenRefine screens, nor for any error/flash state. This spec
   extrapolates the same palette/typography/control-row pattern to those screens since
   they share the same dialog/table/form vocabulary, but that extrapolation is a judgment
   call, not something directly observed in a reference image.
