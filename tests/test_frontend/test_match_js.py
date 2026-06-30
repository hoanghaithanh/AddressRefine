"""Playwright-driven tests for app/static/js/match.js's client-side
results-table interactions.

Covers AC-M4-21 through AC-M4-23 from
`docs/ba/acceptance-criteria/m4-merge-review.md`. These are pure DOM
interactions (no network calls) so they're tested against the live combined
algorithm/results page, driven through the real upload -> mapping ->
recompute flow so the rendered markup/JS wiring is exactly what ships.

Requires Playwright + a Chromium install (`playwright install chromium`).
If that one-time setup step hasn't been done, every test in this module is
skipped at collection time rather than failing — see `_playwright_available`.
"""

from __future__ import annotations

import socket
import threading
import time

import pytest
import uvicorn

CSV_BYTES = (
    b"StreetAddress,ZipCode,City\n"
    b"123 Main St,00501,Springfield\n"
    b"123 MAIN ST.,00501,Springfield\n"
    b"456 Oak Ave,00502,Shelbyville\n"
)


def _playwright_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _playwright_available(),
    reason="Playwright/Chromium not available in this environment",
)


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture(scope="module")
def live_server():
    """Run the real app via uvicorn in a background thread for the duration
    of this module's tests."""
    from app.main import app

    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 10
    import urllib.request

    while time.time() < deadline:
        try:
            urllib.request.urlopen(base_url + "/", timeout=0.5)
            break
        except Exception:
            time.sleep(0.1)
    else:
        pytest.fail("Live server did not start in time")

    yield base_url

    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture
def page_with_results_table(live_server):
    """Drive a fresh browser context through upload -> mapping -> fingerprint
    recompute so a results table with one candidate pair is rendered, then
    yield the Playwright Page positioned on /algorithm."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        page.goto(live_server + "/")
        page.set_input_files(
            'input[type="file"]',
            files=[{"name": "addresses.csv", "mimeType": "text/csv", "buffer": CSV_BYTES}],
        )
        page.click('button:has-text("Upload")')

        page.wait_for_selector("#street_col")
        page.select_option("#street_col", "StreetAddress")
        page.select_option("#zip_col", "ZipCode")
        page.select_option("#city_col", "City")
        page.click('button:has-text("Save mapping")')

        page.wait_for_selector(".pair-row")

        yield page

        context.close()
        browser.close()


# ---------------------------------------------------------------------------
# AC-M4-21 — checking "Merge?" without a prior address click defaults
# "New cell value" to the first-listed address
# ---------------------------------------------------------------------------


def test_checking_merge_without_clicking_address_defaults_new_cell_value_to_first_address(
    page_with_results_table,
):
    page = page_with_results_table
    row = page.locator(".pair-row").first

    new_value_input = row.locator(".pair-row-new-value")
    assert new_value_input.input_value() == ""

    first_address_button = row.locator(".pair-row-address").first
    first_address_text = first_address_button.get_attribute("data-address")

    row.locator(".pair-row-checkbox").check()

    assert new_value_input.input_value() == first_address_text
    assert row.locator(".pair-row-checkbox").is_checked()


# ---------------------------------------------------------------------------
# AC-M4-22 — clicking either address sets "New cell value" and auto-checks
# "Merge?"
# ---------------------------------------------------------------------------


def test_clicking_either_address_sets_new_cell_value_and_checks_merge_checkbox(
    page_with_results_table,
):
    page = page_with_results_table
    row = page.locator(".pair-row").first

    second_address_button = row.locator(".pair-row-address").nth(1)
    second_address_text = second_address_button.get_attribute("data-address")

    assert not row.locator(".pair-row-checkbox").is_checked()

    second_address_button.click()

    new_value_input = row.locator(".pair-row-new-value")
    assert new_value_input.input_value() == second_address_text
    assert row.locator(".pair-row-checkbox").is_checked()


def test_clicking_address_overrides_prior_checkbox_state_regardless(page_with_results_table):
    """AC-M4-22: clicking an address sets New cell value + checks Merge?
    "regardless of its prior state" -- verify this holds even when the
    checkbox was already checked via the AC-M4-21 default-fill path."""
    page = page_with_results_table
    row = page.locator(".pair-row").first

    row.locator(".pair-row-checkbox").check()
    first_address_text = row.locator(".pair-row-new-value").input_value()

    second_address_button = row.locator(".pair-row-address").nth(1)
    second_address_text = second_address_button.get_attribute("data-address")
    assert second_address_text != first_address_text

    second_address_button.click()

    assert row.locator(".pair-row-new-value").input_value() == second_address_text
    assert row.locator(".pair-row-checkbox").is_checked()


# ---------------------------------------------------------------------------
# AC-M4-23 — "New cell value" remains editable after being defaulted/clicked
# ---------------------------------------------------------------------------


def test_new_cell_value_remains_editable_after_being_defaulted(page_with_results_table):
    page = page_with_results_table
    row = page.locator(".pair-row").first

    row.locator(".pair-row-checkbox").check()
    new_value_input = row.locator(".pair-row-new-value")
    assert new_value_input.input_value() != ""

    new_value_input.fill("A Completely Custom Value")

    assert new_value_input.input_value() == "A Completely Custom Value"
    assert row.locator(".pair-row-checkbox").is_checked()


def test_new_cell_value_remains_editable_after_address_click(page_with_results_table):
    page = page_with_results_table
    row = page.locator(".pair-row").first

    row.locator(".pair-row-address").first.click()
    new_value_input = row.locator(".pair-row-new-value")

    new_value_input.fill("Another Custom Value")

    assert new_value_input.input_value() == "Another Custom Value"
    assert row.locator(".pair-row-checkbox").is_checked()
