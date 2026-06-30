# Design reference material

This directory holds the OpenRefine-style redesign's source material and the synthesized spec derived from it. See issue #10 and `CLAUDE.md`'s Workflow section (chore-loop variant) for how this fits into the BA -> coder -> tester -> reviewer loop.

- `reference/screenshots/` — OpenRefine reference screenshots, named by the OpenRefine feature/screen they capture (not forced into a 1:1 mapping with AddressRefine's 4 screens).
- `reference/html-snippets/` — captured HTML element snippets (`.html` files).
- `reference/design-tokens.md` — raw computed-style notes (colors, fonts, spacing) pulled via a browser extension. Kept raw; synthesis happens in `ui-design-spec.md`.
- `ui-design-spec.md` — authored by the `business-analyst` agent: palette, typography, spacing scale, component inventory, interaction states, and an explicit mapping from OpenRefine reference elements to AddressRefine screens/components. Does not exist yet — created during the BA pass for this chore.
