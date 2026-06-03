"""Browser automation helpers for filling extracted URL forms."""

import json
import re
from dataclasses import asdict, dataclass
from email.utils import parseaddr
from pathlib import Path
from urllib.parse import urlparse

from gmail_client import Email


@dataclass
class FieldValueRule:
    key: str
    source: str
    regex: str | None = None
    group: int = 1
    default: str | None = None


@dataclass
class FormFieldRule:
    field_key: str
    selector_strategy: str
    selector_value: str
    selector_name: str | None = None
    input_type: str = "text"
    required: bool = True
    requires_manual_input: bool = False


@dataclass
class FormAutomationConfig:
    url_allowlist: list[str]
    headless: bool
    timeout_ms: int
    field_values: list[FieldValueRule]
    form_fields: list[FormFieldRule]
    submit_selector: dict | None
    manual_after_fill: bool = False


@dataclass
class DiscoveredInput:
    selector: str
    tag: str
    type: str
    name: str
    id: str
    label: str
    placeholder: str
    aria_label: str
    required: bool
    disabled: bool
    visible: bool
    options: list[str]


@dataclass
class FormAutomationResult:
    email_id: str
    url: str
    discovered_inputs: list[dict]
    filled_fields: list[str]
    missing_required_fields: list[str]
    submitted: bool
    final_url: str
    status: str
    error: str | None = None


TEXT_INPUT_TYPES = {
    "text",
    "textarea",
    "date",
    "time",
    "datetime-local",
    "number",
    "email",
    "tel",
    "password",
    "search",
    "url",
    "contenteditable",
}

SELECTOR_STRATEGIES = {"label", "placeholder", "name", "id", "css", "role", "test_id"}


def load_form_automation_config(path: str) -> FormAutomationConfig:
    """Load and validate a form automation JSON config file."""
    config_path = Path(path)
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Form automation config not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in form automation config: {path}") from exc

    if not isinstance(raw, dict):
        raise ValueError("Form automation config must be a JSON object.")

    allowlist = raw.get("url_allowlist")
    if not isinstance(allowlist, list) or not allowlist:
        raise ValueError("Form automation config requires non-empty url_allowlist.")
    if not all(isinstance(host, str) and host.strip() for host in allowlist):
        raise ValueError("url_allowlist must contain non-empty hostnames.")

    field_values = _load_field_value_rules(raw.get("field_values", []))
    form_fields = _load_form_field_rules(raw.get("form_fields", []))
    submit_selector = raw.get("submit_selector")
    if submit_selector is not None and not isinstance(submit_selector, dict):
        raise ValueError("submit_selector must be an object when provided.")

    return FormAutomationConfig(
        url_allowlist=[host.strip().lower() for host in allowlist],
        headless=bool(raw.get("headless", True)),
        timeout_ms=int(raw.get("timeout_ms", 30000)),
        field_values=field_values,
        form_fields=form_fields,
        submit_selector=submit_selector,
        manual_after_fill=bool(raw.get("manual_after_fill", False)),
    )


def build_email_context(email: Email) -> dict[str, str]:
    """Build source values that field extraction rules can reference."""
    _, sender_email = parseaddr(email.sender)
    return {
        "id": email.id,
        "thread_id": email.thread_id,
        "subject": email.subject,
        "sender": email.sender,
        "sender_email": sender_email,
        "date": email.date,
        "snippet": email.snippet,
        "body": email.body,
        "links_joined": "\n".join(email.links),
        "first_link": email.links[0] if email.links else "",
    }


def extract_invoice_lookup_code(text: str) -> str | None:
    """Extract a Petrolimex invoice lookup code from email body text."""
    match = re.search(r"Mã\s+tra\s+cứu\s*:\s*([^\s\r\n]+)", text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def resolve_field_values(
    email: Email, config: FormAutomationConfig
) -> dict[str, str]:
    """Resolve configured form field values from an email."""
    context = build_email_context(email)
    values: dict[str, str] = {}

    for rule in config.field_values:
        if rule.source == "petrolimex_invoice_code":
            invoice_code = extract_invoice_lookup_code(email.body)
            if invoice_code:
                values[rule.key] = invoice_code
            elif rule.default is not None:
                values[rule.key] = rule.default
            else:
                raise ValueError("Petrolimex invoice lookup code not found in email body.")
            continue

        if rule.source not in context:
            raise ValueError(f"Unknown field value source: {rule.source}")

        source_value = context[rule.source]
        if rule.regex:
            match = re.search(rule.regex, source_value, flags=re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    values[rule.key] = match.group(rule.group).strip()
                except IndexError as exc:
                    raise ValueError(
                        f"Regex group {rule.group} not found for field {rule.key}."
                    ) from exc
            elif rule.default is not None:
                values[rule.key] = rule.default
            else:
                raise ValueError(f"Regex did not match for field {rule.key}.")
        else:
            value = source_value.strip()
            values[rule.key] = value if value else (rule.default or "")

    return values


def select_email_url(email: Email, link_index: int) -> str | None:
    """Return the selected HTTPS URL from an email's extracted links."""
    if link_index < 0:
        return None

    https_links = [
        link for link in email.links if urlparse(link).scheme.lower() == "https"
    ]
    if link_index >= len(https_links):
        return None
    return https_links[link_index]


def is_allowed_url(url: str, allowlist: list[str]) -> bool:
    """Return whether a URL host is allowlisted."""
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme.lower() != "https" or not hostname:
        return False

    for allowed_host in allowlist:
        allowed = allowed_host.lower().strip()
        if hostname == allowed or hostname.endswith(f".{allowed}"):
            return True
    return False


def discover_inputs(page) -> list[DiscoveredInput]:
    """Discover supported form input metadata from the current page."""
    inputs = page.eval_on_selector_all(
        'input, textarea, select, [contenteditable="true"]',
        """
        elements => elements.map((element, index) => {
          const tag = element.tagName.toLowerCase();
          const type = (element.getAttribute("type") || tag).toLowerCase();
          const id = element.getAttribute("id") || "";
          const name = element.getAttribute("name") || "";
          const labelNode = id
            ? document.querySelector(`label[for="${CSS.escape(id)}"]`)
            : element.closest("label");
          const rect = element.getBoundingClientRect();
          const options = tag === "select"
            ? Array.from(element.options).map(option => option.value || option.text)
            : [];
          return {
            selector: id ? `[id="${id.replaceAll('"', '\\\\"')}"]`
              : name ? `[name="${name.replaceAll('"', '\\\\"')}"]`
              : `${tag}:nth-of-type(${index + 1})`,
            tag,
            type,
            name,
            id,
            label: labelNode ? labelNode.textContent.trim().replace(/\\s+/g, " ") : "",
            placeholder: element.getAttribute("placeholder") || "",
            aria_label: element.getAttribute("aria-label") || "",
            required: Boolean(element.required),
            disabled: Boolean(element.disabled),
            visible: Boolean(rect.width && rect.height),
            options
          };
        })
        """,
    )
    return [DiscoveredInput(**input_data) for input_data in inputs]


def locator_for_rule(page, rule: FormFieldRule):
    """Return a Playwright locator for a configured field rule."""
    strategy = rule.selector_strategy
    if strategy == "label":
        return page.get_by_label(rule.selector_value)
    if strategy == "placeholder":
        return page.get_by_placeholder(rule.selector_value)
    if strategy == "name":
        return page.locator(f'[name="{_css_attr_escape(rule.selector_value)}"]')
    if strategy == "id":
        return page.locator(f'[id="{_css_attr_escape(rule.selector_value)}"]')
    if strategy == "css":
        return page.locator(rule.selector_value)
    if strategy == "role":
        role = rule.selector_name or rule.input_type
        return page.get_by_role(role, name=re.compile(rule.selector_value, re.IGNORECASE))
    if strategy == "test_id":
        return page.get_by_test_id(rule.selector_value)
    raise ValueError(f"Unsupported selector strategy: {strategy}")


def fill_field(page, rule: FormFieldRule, value: str) -> None:
    """Fill one field using the configured field type."""
    locator = locator_for_rule(page, rule)
    input_type = rule.input_type.lower()

    if input_type in TEXT_INPUT_TYPES:
        locator.fill(value)
        return
    if input_type in {"checkbox", "radio"}:
        if _string_to_bool(value):
            locator.check()
        return
    if input_type == "select":
        locator.select_option(value)
        return

    raise ValueError(f"Unsupported input type: {rule.input_type}")


def submit_page(page, submit_selector: dict | None) -> bool:
    """Submit the current page by clicking a configured or unique submit control."""
    if submit_selector:
        rule = FormFieldRule(
            field_key="submit",
            selector_strategy=submit_selector.get("selector_strategy", "css"),
            selector_value=submit_selector.get("selector_value", ""),
            selector_name=submit_selector.get("selector_name"),
            input_type="button",
            required=True,
        )
        locator_for_rule(page, rule).click()
        return True

    submit_controls = page.locator(
        'button[type="submit"], input[type="submit"], button:has-text("Submit"), '
        'button:has-text("Tra cứu"), button:has-text("Search"), '
        'button:has-text("Continue")'
    )
    if submit_controls.count() == 1:
        submit_controls.first.click()
        return True
    return False


def wait_for_manual_completion(
    page, config: FormAutomationConfig, submit: bool
) -> bool:
    """Wait for the user to complete manual fields before optional submission."""
    input("Press Enter after entering captcha in the browser...")
    if submit:
        return submit_page(page, config.submit_selector)
    return False


def automate_email_form(
    email: Email, config: FormAutomationConfig, link_index: int, submit: bool
) -> FormAutomationResult:
    """Automate the selected extracted URL for a single email."""
    url = select_email_url(email, link_index)
    if not url:
        return _result(email.id, "", "skipped", "No HTTPS URL found at link index.")
    if not is_allowed_url(url, config.url_allowlist):
        return _result(email.id, url, "skipped", "URL hostname is not allowlisted.")

    try:
        field_values = resolve_field_values(email, config)
    except ValueError as exc:
        return _result(email.id, url, "failed", str(exc))

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=False if config.manual_after_fill else config.headless
            )
            try:
                context = browser.new_context()
                try:
                    page = context.new_page()
                    page.set_default_timeout(config.timeout_ms)
                    page.goto(url, wait_until="domcontentloaded")

                    discovered = [asdict(item) for item in discover_inputs(page)]
                    filled_fields = []
                    missing_required_fields = []

                    for rule in config.form_fields:
                        if rule.requires_manual_input:
                            continue

                        value = field_values.get(rule.field_key, "")
                        if not value:
                            if rule.required:
                                missing_required_fields.append(rule.field_key)
                            continue
                        fill_field(page, rule, value)
                        filled_fields.append(rule.field_key)

                    submitted = False
                    if config.manual_after_fill and not missing_required_fields:
                        submitted = wait_for_manual_completion(page, config, submit)
                    elif submit and not missing_required_fields:
                        submitted = submit_page(page, config.submit_selector)

                    status = "submitted" if submitted else "filled"
                    if missing_required_fields:
                        status = "failed"

                    return FormAutomationResult(
                        email_id=email.id,
                        url=url,
                        discovered_inputs=discovered,
                        filled_fields=filled_fields,
                        missing_required_fields=missing_required_fields,
                        submitted=submitted,
                        final_url=page.url,
                        status=status,
                        error=(
                            "Missing required field values."
                            if missing_required_fields
                            else None
                        ),
                    )
                finally:
                    context.close()
            finally:
                browser.close()
    except Exception as exc:
        return _result(email.id, url, "failed", str(exc))


def automate_email_forms(
    emails: list[Email], config_path: str, link_index: int, submit: bool
) -> list[FormAutomationResult]:
    """Run form automation for a list of emails."""
    config = load_form_automation_config(config_path)
    return [
        automate_email_form(email, config, link_index, submit)
        for email in emails
    ]


def write_automation_results(
    results: list[FormAutomationResult], output_path: str
) -> None:
    """Write automation results as indented UTF-8 JSON."""
    data = [asdict(result) for result in results]
    with Path(output_path).open("w", encoding="utf-8") as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=2)


def _load_field_value_rules(raw_rules) -> list[FieldValueRule]:
    if not isinstance(raw_rules, list):
        raise ValueError("field_values must be a list.")

    rules = []
    for raw_rule in raw_rules:
        if not isinstance(raw_rule, dict):
            raise ValueError("Each field_values item must be an object.")
        try:
            rules.append(
                FieldValueRule(
                    key=raw_rule["key"],
                    source=raw_rule["source"],
                    regex=raw_rule.get("regex"),
                    group=int(raw_rule.get("group", 1)),
                    default=raw_rule.get("default"),
                )
            )
        except KeyError as exc:
            raise ValueError(
                f"Field value rule missing required key: {exc.args[0]}"
            ) from exc
    return rules


def _load_form_field_rules(raw_rules) -> list[FormFieldRule]:
    if not isinstance(raw_rules, list):
        raise ValueError("form_fields must be a list.")

    rules = []
    for raw_rule in raw_rules:
        if not isinstance(raw_rule, dict):
            raise ValueError("Each form_fields item must be an object.")
        try:
            strategy = raw_rule["selector_strategy"]
            if strategy not in SELECTOR_STRATEGIES:
                raise ValueError(f"Unsupported selector strategy: {strategy}")
            rules.append(
                FormFieldRule(
                    field_key=raw_rule["field_key"],
                    selector_strategy=strategy,
                    selector_value=raw_rule["selector_value"],
                    selector_name=raw_rule.get("selector_name"),
                    input_type=raw_rule.get("input_type", "text"),
                    required=bool(raw_rule.get("required", True)),
                    requires_manual_input=bool(
                        raw_rule.get("requires_manual_input", False)
                    ),
                )
            )
        except KeyError as exc:
            raise ValueError(
                f"Form field rule missing required key: {exc.args[0]}"
            ) from exc
    return rules


def _result(
    email_id: str, url: str, status: str, error: str | None = None
) -> FormAutomationResult:
    return FormAutomationResult(
        email_id=email_id,
        url=url,
        discovered_inputs=[],
        filled_fields=[],
        missing_required_fields=[],
        submitted=False,
        final_url=url,
        status=status,
        error=error,
    )


def _css_attr_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _string_to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on", "checked"}
