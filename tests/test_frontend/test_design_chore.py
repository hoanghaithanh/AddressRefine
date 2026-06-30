"""Tests for the OpenRefine-style frontend redesign chore (issue #10).

Covers the objective/code-checkable acceptance criteria AC-CHORE-1 through
AC-CHORE-9 from `docs/ba/acceptance-criteria/chore-frontend-redesign.md`.
AC-CHORE-10 (no functional regression) is verified by re-running the full
pre-existing pytest suite, not by a dedicated test here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.conftest import sample_csv_bytes

REPO_ROOT = Path(__file__).resolve().parents[2]
CSS_PATH = REPO_ROOT / "app" / "static" / "css" / "styles.css"
TEMPLATES_DIR = REPO_ROOT / "app" / "templates"


def _css_text() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def _root_block_text() -> str:
    """Return the raw text content of the :root { ... } block in styles.css."""
    css = _css_text()
    match = re.search(r":root\s*\{(.*?)\}", css, flags=re.DOTALL)
    assert match, "No :root block found in styles.css"
    return match.group(1)


# ---------------------------------------------------------------------------
# AC-CHORE-1 — Required CSS custom properties exist with specified values
# ---------------------------------------------------------------------------

EXPECTED_COLOR_VARS = {
    "--color-bg": "#eeeeee",
    "--color-surface": "#ffffff",
    "--color-header-bg": "#e3edfb",
    "--color-header-border": "#a9c6ee",
    "--color-text": "#1f1f1f",
    "--color-border": "#cccccc",
    "--color-primary": "#4a4a4a",
    "--color-primary-hover": "#333333",
    "--color-secondary-bg": "#f4f4f4",
    "--color-table-header-bg": "#e0e0e0",
    "--color-table-row-odd": "#eeeeee",
    "--color-table-row-even": "#ffffff",
    "--color-muted": "#767676",
    "--color-link": "#1a4fa0",
}


@pytest.mark.parametrize("var_name, expected_value", sorted(EXPECTED_COLOR_VARS.items()))
def test_root_color_custom_property_has_spec_value(var_name, expected_value):
    """AC-CHORE-1: each required color custom property exists with the spec'd hex value."""
    root_text = _root_block_text()
    pattern = re.compile(re.escape(var_name) + r"\s*:\s*([^;]+);", re.IGNORECASE)
    match = pattern.search(root_text)
    assert match, f"{var_name} not declared in :root block"
    actual_value = match.group(1).strip().lower()
    assert actual_value == expected_value.lower()


def test_css_braces_are_balanced():
    """Sanity check: styles.css has balanced braces (catches stray braces/typos)."""
    css = _css_text()
    assert css.count("{") == css.count("}")
    assert css.count("{") > 0


# ---------------------------------------------------------------------------
# AC-CHORE-2 — Required spacing custom properties exist
# ---------------------------------------------------------------------------

EXPECTED_SPACE_VARS = {
    "--space-xs": "0.25rem",
    "--space-sm": "0.5rem",
    "--space-md": "0.75rem",
    "--space-lg": "1rem",
    "--space-xl": "1.5rem",
}


@pytest.mark.parametrize("var_name, expected_value", sorted(EXPECTED_SPACE_VARS.items()))
def test_root_space_custom_property_has_spec_value(var_name, expected_value):
    """AC-CHORE-2: each required spacing custom property exists with the spec'd value."""
    root_text = _root_block_text()
    pattern = re.compile(re.escape(var_name) + r"\s*:\s*([^;]+);", re.IGNORECASE)
    match = pattern.search(root_text)
    assert match, f"{var_name} not declared in :root block"
    actual_value = match.group(1).strip().lower()
    assert actual_value == expected_value.lower()


# ---------------------------------------------------------------------------
# AC-CHORE-3 — No inline style= attributes in any shipped template
# ---------------------------------------------------------------------------


def _all_template_files() -> list[Path]:
    return sorted(TEMPLATES_DIR.rglob("*.html"))


def test_at_least_one_template_file_found():
    """Guard against an empty glob silently passing the no-inline-style test below."""
    assert len(_all_template_files()) >= 5


@pytest.mark.parametrize("template_path", _all_template_files(), ids=lambda p: p.name)
def test_template_has_no_inline_style_attribute(template_path):
    """AC-CHORE-3: no `style="` or `style='` attribute appears in any shipped template."""
    text = template_path.read_text(encoding="utf-8")
    assert not re.search(r"""\sstyle\s*=\s*['"]""", text), (
        f"{template_path} contains an inline style= attribute"
    )


# ---------------------------------------------------------------------------
# AC-CHORE-4 — Header banner uses the new header colors
# ---------------------------------------------------------------------------


def test_base_html_has_site_header_class():
    text = (TEMPLATES_DIR / "base.html").read_text(encoding="utf-8")
    assert '<header class="site-header">' in text


def test_site_header_css_rule_uses_header_color_vars():
    """AC-CHORE-4: .site-header's background/border-bottom reference the header color vars."""
    css = _css_text()
    match = re.search(r"\.site-header\s*\{([^}]*)\}", css)
    assert match, ".site-header rule not found in styles.css"
    rule_body = match.group(1)
    assert "var(--color-header-bg)" in rule_body
    assert "var(--color-header-border)" in rule_body


# ---------------------------------------------------------------------------
# AC-CHORE-5 — Mapping form fields grouped in .control-row / .control-group
# ---------------------------------------------------------------------------


def test_mapping_html_groups_fields_in_control_row_and_groups():
    text = (TEMPLATES_DIR / "mapping.html").read_text(encoding="utf-8")

    assert '<div class="control-row">' in text
    control_row_start = text.index('<div class="control-row">')
    form_end = text.index("</form>", control_row_start)
    row_body = text[control_row_start:form_end]

    assert row_body.count('class="control-group"') == 4

    for field, select_attrs in [
        ("street_col", 'id="street_col" name="street_col" required class="field"'),
        ("zip_col", 'id="zip_col" name="zip_col" class="field"'),
        ("city_col", 'id="city_col" name="city_col" class="field"'),
        ("country_col", 'id="country_col" name="country_col" class="field"'),
    ]:
        assert select_attrs in text, f"unexpected/missing attrs on {field} select"


def test_mapping_html_select_attrs_unchanged_from_pre_chore():
    """AC-CHORE-5: name=, id=, required attrs on each <select> match the pre-chore file."""
    text = (TEMPLATES_DIR / "mapping.html").read_text(encoding="utf-8")

    # street_col is the only required field; the others must NOT carry required=.
    assert re.search(r'<select id="street_col" name="street_col" required', text)
    for field in ("zip_col", "city_col", "country_col"):
        select_tag_match = re.search(rf"<select[^>]*name=\"{field}\"[^>]*>", text)
        assert select_tag_match, f"select for {field} not found"
        assert "required" not in select_tag_match.group(0)


# ---------------------------------------------------------------------------
# AC-CHORE-6 — Algorithm form fields grouped in .control-row / .control-group
# ---------------------------------------------------------------------------


def test_algorithm_html_groups_fields_in_control_row_and_groups():
    """The algorithm select, the n field, and the conditionally-rendered threshold
    field are each wrapped in their own .control-group in the raw Jinja source
    (the threshold one only actually renders when selected_key is a NN algorithm,
    but its markup is present in the template source either way)."""
    text = (TEMPLATES_DIR / "algorithm.html").read_text(encoding="utf-8")
    assert '<div class="control-row">' in text
    assert text.count('class="control-group"') == 3  # algorithm select + n + threshold


def test_algorithm_html_input_attrs_unchanged_from_pre_chore():
    """AC-CHORE-6: name=, id=, min=, max=, step= on n/threshold inputs are unchanged."""
    text = (TEMPLATES_DIR / "algorithm.html").read_text(encoding="utf-8")

    n_input_match = re.search(r'<input[^>]*id="n"[^>]*>', text, re.DOTALL)
    assert n_input_match
    n_input = n_input_match.group(0)
    assert 'name="n"' in n_input
    assert 'min="1"' in n_input
    assert 'step="1"' in n_input

    threshold_input_match = re.search(r'<input[^>]*id="threshold"[^>]*>', text, re.DOTALL)
    assert threshold_input_match
    threshold_input = threshold_input_match.group(0)
    assert 'name="threshold"' in threshold_input
    assert "min=\"{% if selected_key == 'ncd' %}1{% else %}0{% endif %}\"" in threshold_input
    assert 'max="{% if selected_key == \'ncd\' %}10{% endif %}"' in threshold_input
    assert 'step="1"' in threshold_input

    # Jinja conditional governing threshold visibility is preserved.
    assert "{% if selected_key in nn_keys %}" in text
    assert '<input type="hidden" name="threshold" value="">' in text


def test_algorithm_html_renders_with_n_and_threshold_fields_inside_control_groups(client):
    """Integration check: rendered HTML for an NN algorithm has both control-groups
    populated with their respective fields, confirming the Jinja conditional still works
    post-restyle."""
    client.post(
        "/upload",
        files={"file": ("addresses.csv", sample_csv_bytes(), "text/csv")},
        follow_redirects=False,
    )
    client.post(
        "/mapping",
        data={"street_col": "StreetAddress", "zip_col": "ZipCode"},
        follow_redirects=False,
    )
    # Select levenshtein first so GET /algorithm renders the threshold field this time.
    client.post(
        "/algorithm",
        data={"algorithm_key": "levenshtein", "threshold": "3"},
        follow_redirects=False,
    )

    response = client.get("/algorithm")

    assert response.status_code == 200
    text = response.text
    assert 'id="n"' in text
    assert 'id="threshold"' in text
    assert text.count('class="control-group"') == 3  # algorithm + n + threshold this time


# ---------------------------------------------------------------------------
# AC-CHORE-7 — Submit buttons carry .btn and .btn-primary
# ---------------------------------------------------------------------------


def _flow_to_results(client):
    client.post(
        "/upload",
        files={"file": ("addresses.csv", sample_csv_bytes(), "text/csv")},
        follow_redirects=False,
    )
    client.post(
        "/mapping",
        data={"street_col": "StreetAddress", "zip_col": "ZipCode"},
        follow_redirects=False,
    )
    client.post("/algorithm", data={"algorithm_key": "fingerprint"}, follow_redirects=False)


def test_upload_button_has_btn_and_btn_primary(client):
    response = client.get("/")
    assert response.status_code == 200
    match = re.search(r"<button[^>]*>Upload</button>", response.text)
    assert match
    classes = re.search(r'class="([^"]*)"', match.group(0)).group(1).split()
    assert "btn" in classes
    assert "btn-primary" in classes


def test_mapping_button_has_btn_and_btn_primary(client):
    client.post(
        "/upload",
        files={"file": ("addresses.csv", sample_csv_bytes(), "text/csv")},
        follow_redirects=False,
    )
    response = client.get("/mapping")
    assert response.status_code == 200
    match = re.search(r"<button[^>]*>Save mapping</button>", response.text)
    assert match
    classes = re.search(r'class="([^"]*)"', match.group(0)).group(1).split()
    assert "btn" in classes
    assert "btn-primary" in classes


def test_algorithm_button_has_btn_and_btn_primary(client):
    client.post(
        "/upload",
        files={"file": ("addresses.csv", sample_csv_bytes(), "text/csv")},
        follow_redirects=False,
    )
    client.post(
        "/mapping",
        data={"street_col": "StreetAddress", "zip_col": "ZipCode"},
        follow_redirects=False,
    )
    response = client.get("/algorithm")
    assert response.status_code == 200
    match = re.search(r"<button[^>]*>Run matching</button>", response.text)
    assert match
    classes = re.search(r'class="([^"]*)"', match.group(0)).group(1).split()
    assert "btn" in classes
    assert "btn-primary" in classes


# ---------------------------------------------------------------------------
# AC-CHORE-8 — Results table header shading / zebra rows / hover defined
# ---------------------------------------------------------------------------


def test_results_table_header_uses_table_header_bg_var():
    css = _css_text()
    match = re.search(r"\.results-table\s+thead\s+th\s*\{([^}]*)\}", css)
    assert match, ".results-table thead th rule not found"
    assert "var(--color-table-header-bg)" in match.group(1)


def test_results_table_zebra_rules_use_row_color_vars():
    css = _css_text()
    odd_match = re.search(
        r"\.results-table\s+tbody\s+tr:nth-child\(odd\)\s*\{([^}]*)\}", css
    )
    even_match = re.search(
        r"\.results-table\s+tbody\s+tr:nth-child\(even\)\s*\{([^}]*)\}", css
    )
    assert odd_match, "tr:nth-child(odd) rule not found"
    assert even_match, "tr:nth-child(even) rule not found"
    assert "var(--color-table-row-odd)" in odd_match.group(1)
    assert "var(--color-table-row-even)" in even_match.group(1)


def test_results_table_hover_rule_distinct_from_zebra_shades():
    css = _css_text()
    hover_match = re.search(r"\.results-table\s+tbody\s+tr:hover\s*\{([^}]*)\}", css)
    assert hover_match, "tbody tr:hover rule not found"
    hover_body = hover_match.group(1)
    bg_match = re.search(r"background\s*:\s*([^;]+);", hover_body)
    assert bg_match, "tr:hover rule has no background declaration"
    hover_bg = bg_match.group(1).strip().lower()

    assert hover_bg != EXPECTED_COLOR_VARS["--color-table-row-odd"].lower()
    assert hover_bg != EXPECTED_COLOR_VARS["--color-table-row-even"].lower()
    assert "var(--color-table-row-odd)" not in hover_bg
    assert "var(--color-table-row-even)" not in hover_bg


def test_results_table_renders_with_results_table_class(client):
    """Integration check that .results-table actually appears on a populated results page."""
    csv_bytes = b"StreetAddress,ZipCode\n123 Main St,00501\n123 MAIN ST.,00501\n456 Oak Ave,00502\n"
    client.post(
        "/upload",
        files={"file": ("addresses.csv", csv_bytes, "text/csv")},
        follow_redirects=False,
    )
    client.post(
        "/mapping",
        data={"street_col": "StreetAddress", "zip_col": "ZipCode"},
        follow_redirects=False,
    )
    client.post("/algorithm", data={"algorithm_key": "fingerprint"}, follow_redirects=False)

    response = client.get("/results")
    assert response.status_code == 200
    assert '<table class="results-table">' in response.text


# ---------------------------------------------------------------------------
# AC-CHORE-9 — Disabled Accept/Reject buttons carry a visible disabled treatment
# ---------------------------------------------------------------------------


def test_pair_row_buttons_carry_btn_class_and_disabled_attr():
    text = (TEMPLATES_DIR / "partials" / "_pair_row.html").read_text(encoding="utf-8")
    accept_match = re.search(r"<button[^>]*>Accept</button>", text)
    reject_match = re.search(r"<button[^>]*>Reject</button>", text)
    assert accept_match and reject_match

    accept_tag, reject_tag = accept_match.group(0), reject_match.group(0)
    assert "disabled" in accept_tag
    assert "disabled" in reject_tag

    accept_classes = re.search(r'class="([^"]*)"', accept_tag).group(1).split()
    reject_classes = re.search(r'class="([^"]*)"', reject_tag).group(1).split()
    assert "btn" in accept_classes
    assert "btn" in reject_classes
    assert "btn-primary" in accept_classes
    assert "btn-secondary" in reject_classes


def test_btn_disabled_css_rule_has_reduced_opacity_or_muted_color():
    css = _css_text()
    match = re.search(r"\.btn:disabled\s*\{([^}]*)\}", css)
    assert match, ".btn:disabled rule not found"
    rule_body = match.group(1)
    opacity_match = re.search(r"opacity\s*:\s*0(\.\d+)?\s*;", rule_body)
    has_opacity = bool(opacity_match) and "opacity: 1" not in rule_body
    has_muted_color = "var(--color-muted)" in rule_body
    assert has_opacity or has_muted_color, (
        ".btn:disabled does not declare a reduced-opacity or muted-color treatment"
    )


def test_btn_disabled_rule_distinct_from_btn_primary_enabled_appearance():
    """The disabled rule's background must differ from .btn-primary's enabled appearance,
    i.e. it must not just be identical flat styling with no visible distinction."""
    css = _css_text()
    disabled_match = re.search(r"\.btn:disabled\s*\{([^}]*)\}", css)
    assert disabled_match
    disabled_body = disabled_match.group(1)
    # Spec requires opacity 0.5 (or muted color) to visually separate the disabled
    # state from the otherwise-identical flat-gray enabled background.
    assert "opacity: 0.5" in disabled_body or "var(--color-muted)" in disabled_body


def test_disabled_buttons_render_on_results_page(client):
    """Integration check: rendered results page actually has the disabled buttons with
    the btn class so the CSS rule applies to them in practice."""
    csv_bytes = b"StreetAddress,ZipCode\n123 Main St,00501\n123 MAIN ST.,00501\n456 Oak Ave,00502\n"
    client.post(
        "/upload",
        files={"file": ("addresses.csv", csv_bytes, "text/csv")},
        follow_redirects=False,
    )
    client.post(
        "/mapping",
        data={"street_col": "StreetAddress", "zip_col": "ZipCode"},
        follow_redirects=False,
    )
    client.post("/algorithm", data={"algorithm_key": "fingerprint"}, follow_redirects=False)

    response = client.get("/results")
    assert response.status_code == 200
    text = response.text
    assert '<button type="button" class="btn btn-primary" disabled>Accept</button>' in text
    assert '<button type="button" class="btn btn-secondary" disabled>Reject</button>' in text


# ---------------------------------------------------------------------------
# Field focus state sanity check (spec component-inventory row: .field :focus)
# ---------------------------------------------------------------------------


def test_field_focus_rule_exists_and_differs_from_default():
    css = _css_text()
    focus_match = re.search(r"\.field:focus,[^{]*\{([^}]*)\}", css)
    assert focus_match, "No :focus rule found for .field/select/input"
    assert "var(--color-primary)" in focus_match.group(1)
