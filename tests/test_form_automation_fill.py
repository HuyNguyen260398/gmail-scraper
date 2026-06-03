import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from form_automation import FormFieldRule, fill_field, locator_for_rule, submit_page


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
