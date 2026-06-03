import re
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from form_automation import (
    FieldValueRule,
    FormAutomationConfig,
    FormFieldRule,
    automate_email_form,
    fill_field,
    locator_for_rule,
    submit_page,
)
from gmail_client import Email


class FakeLocator:
    def __init__(self, name="locator", count_value=1):
        self.name = name
        self.count_value = count_value
        self.calls = []

    @property
    def first(self):
        self.calls.append(("first",))
        return self

    def fill(self, value):
        self.calls.append(("fill", value))

    def check(self):
        self.calls.append(("check",))

    def select_option(self, value):
        self.calls.append(("select_option", value))

    def click(self):
        self.calls.append(("click",))

    def count(self):
        self.calls.append(("count",))
        return self.count_value


class FakePage:
    def __init__(self):
        self.calls = []
        self.last_locator = None
        self.submit_locator = FakeLocator("submit")

    def _record(self, call):
        self.calls.append(call)
        self.last_locator = FakeLocator(str(call))
        return self.last_locator

    def get_by_label(self, value):
        return self._record(("label", value))

    def get_by_placeholder(self, value):
        return self._record(("placeholder", value))

    def get_by_role(self, role, name=None):
        assert isinstance(name, re.Pattern)
        return self._record(("role", role, name.pattern))

    def get_by_test_id(self, value):
        return self._record(("test_id", value))

    def locator(self, selector):
        if "button" in selector and "submit" in selector.lower():
            self.calls.append(("locator", selector))
            return self.submit_locator
        return self._record(("locator", selector))


class FakeBrowserPage(FakePage):
    def __init__(self):
        super().__init__()
        self.url = "about:blank"
        self.timeout_ms = None

    def set_default_timeout(self, timeout_ms):
        self.timeout_ms = timeout_ms

    def goto(self, url, wait_until=None):
        self.url = url
        self.calls.append(("goto", url, wait_until))

    def eval_on_selector_all(self, selector, script):
        self.calls.append(("eval_on_selector_all", selector))
        return []


class FakeContext:
    def __init__(self, page):
        self.page = page
        self.closed = False

    def new_page(self):
        return self.page

    def close(self):
        self.closed = True


class FakeBrowser:
    def __init__(self, state):
        self.state = state
        self.closed = False

    def new_context(self):
        context = FakeContext(self.state["page"])
        self.state["context"] = context
        return context

    def close(self):
        self.closed = True
        self.state["browser_closed"] = True


class FakeChromium:
    def __init__(self, state):
        self.state = state

    def launch(self, headless=True):
        self.state["headless"] = headless
        return FakeBrowser(self.state)


class FakePlaywrightManager:
    def __init__(self, state):
        self.state = state

    def __enter__(self):
        return types.SimpleNamespace(chromium=FakeChromium(self.state))

    def __exit__(self, exc_type, exc, traceback):
        self.state["playwright_closed"] = True


def install_fake_playwright(monkeypatch):
    state = {"page": FakeBrowserPage()}
    module = types.ModuleType("playwright.sync_api")
    module.sync_playwright = lambda: FakePlaywrightManager(state)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", module)
    return state


def sample_email() -> Email:
    return Email(
        id="msg-1",
        thread_id="thread-1",
        subject="Invoice",
        sender="Billing <billing@example.com>",
        date="Wed, 03 Jun 2026 08:00:00 +0700",
        snippet="Code: ABC123",
        body="Code: ABC123",
        labels=["INBOX"],
        links=["https://hoadon.petrolimex.com.vn/SearchInvoicebycode/Index"],
    )


def form_config(*, manual_after_fill=False) -> FormAutomationConfig:
    return FormAutomationConfig(
        url_allowlist=["hoadon.petrolimex.com.vn"],
        headless=True,
        timeout_ms=10000,
        field_values=[
            FieldValueRule("invoice_code", "body", regex=r"Code: ([A-Z0-9]+)")
        ],
        form_fields=[
            FormFieldRule("invoice_code", "id", "strFkey", input_type="text"),
            FormFieldRule(
                "captcha",
                "id",
                "captch",
                input_type="text",
                required=True,
                requires_manual_input=True,
            ),
        ],
        submit_selector={"selector_strategy": "css", "selector_value": "#submit"},
        manual_after_fill=manual_after_fill,
    )


def test_locator_for_rule_supports_label_placeholder_name_id_css_role_and_test_id():
    page = FakePage()

    locator_for_rule(page, FormFieldRule("x", "label", "Invoice"))
    locator_for_rule(page, FormFieldRule("x", "placeholder", "Invoice code"))
    locator_for_rule(page, FormFieldRule("x", "name", "invoice"))
    locator_for_rule(page, FormFieldRule("x", "id", "invoice-id"))
    locator_for_rule(page, FormFieldRule("x", "css", ".invoice"))
    locator_for_rule(page, FormFieldRule("x", "role", "Submit", selector_name="button"))
    locator_for_rule(page, FormFieldRule("x", "test_id", "invoice-input"))

    assert page.calls == [
        ("label", "Invoice"),
        ("placeholder", "Invoice code"),
        ("locator", '[name="invoice"]'),
        ("locator", '[id="invoice-id"]'),
        ("locator", ".invoice"),
        ("role", "button", "Submit"),
        ("test_id", "invoice-input"),
    ]


def test_fill_field_routes_text_checkbox_radio_and_select_inputs():
    page = FakePage()

    fill_field(page, FormFieldRule("code", "label", "Invoice", input_type="text"), "ABC")
    assert page.last_locator.calls[-1] == ("fill", "ABC")

    fill_field(page, FormFieldRule("agree", "label", "Agree", input_type="checkbox"), "true")
    assert page.last_locator.calls[-1] == ("check",)

    fill_field(page, FormFieldRule("size", "label", "Size", input_type="radio"), "yes")
    assert page.last_locator.calls[-1] == ("check",)

    fill_field(page, FormFieldRule("city", "label", "City", input_type="select"), "Hanoi")
    assert page.last_locator.calls[-1] == ("select_option", "Hanoi")


def test_submit_page_clicks_configured_selector():
    page = FakePage()

    assert submit_page(
        page,
        {
            "selector_strategy": "role",
            "selector_name": "button",
            "selector_value": "Submit",
        },
    )

    assert page.last_locator.calls[-1] == ("click",)


def test_submit_page_clicks_unique_detected_submit_control():
    page = FakePage()

    assert submit_page(page, None)

    assert ("count",) in page.submit_locator.calls
    assert ("first",) in page.submit_locator.calls
    assert ("click",) in page.submit_locator.calls


def test_automate_email_form_does_not_fail_when_required_manual_field_has_no_value(monkeypatch):
    state = install_fake_playwright(monkeypatch)

    result = automate_email_form(sample_email(), form_config(), link_index=0, submit=False)

    assert result.status == "filled"
    assert result.filled_fields == ["invoice_code"]
    assert result.missing_required_fields == []
    assert state["page"].last_locator.calls[-1] == ("fill", "ABC123")


def test_automate_email_form_manual_after_fill_forces_visible_browser_and_submits(monkeypatch):
    state = install_fake_playwright(monkeypatch)
    input_prompts = []
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt: input_prompts.append(prompt) or "",
    )

    result = automate_email_form(
        sample_email(), form_config(manual_after_fill=True), link_index=0, submit=True
    )

    assert result.status == "submitted"
    assert result.submitted is True
    assert state["headless"] is False
    assert input_prompts == ["Press Enter after entering captcha in the browser..."]
    assert ("click",) in state["page"].last_locator.calls
