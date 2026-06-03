import sys
from pathlib import Path

import pytest

playwright_sync = pytest.importorskip("playwright.sync_api")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from form_automation import FormFieldRule, fill_field, submit_page


@pytest.mark.playwright
def test_playwright_fills_and_submits_local_static_form():
    playwright_context = playwright_sync.sync_playwright().start()
    try:
        browser = playwright_context.chromium.launch(headless=True)
    except Exception as exc:
        playwright_context.stop()
        pytest.skip(f"Playwright browser unavailable: {exc}")

    try:
        page = browser.new_page()
        page.set_content(
            """
            <form onsubmit="window.submitted = true; return false;">
              <label>Invoice code <input name="invoice"></label>
              <label>City <select name="city"><option>Hanoi</option></select></label>
              <button type="submit">Submit</button>
            </form>
            """
        )

        fill_field(
            page,
            FormFieldRule("invoice", "label", "Invoice code", input_type="text"),
            "INV-123",
        )
        fill_field(
            page,
            FormFieldRule("city", "label", "City", input_type="select"),
            "Hanoi",
        )
        assert submit_page(page, None)

        assert page.locator('[name="invoice"]').input_value() == "INV-123"
        assert page.evaluate("window.submitted") is True
    finally:
        browser.close()
        playwright_context.stop()
