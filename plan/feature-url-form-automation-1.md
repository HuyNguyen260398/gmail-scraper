---
goal: Implement extracted URL form automation from Gmail email content
version: 1.1
date_created: 2026-06-03
last_updated: 2026-06-04
owner: Repository maintainers
status: 'Completed'
tags: [feature, cli, gmail, browser-automation, playwright]
---

# Introduction

![Status: Completed](https://img.shields.io/badge/status-Completed-brightgreen)

This plan defines the implementation steps for opening the URL links extracted from Gmail messages, discovering all form inputs on the target web page, filling those inputs with values parsed from exported JSON content, and optionally submitting the form through browser automation.

The current flow is JSON-first:

1. Fetch Gmail messages and save the full extracted email content to JSON.
2. Save a second JSON handoff file containing the selected URL and extracted `Mã tra cứu` value.
3. Run form automation from that handoff JSON so the browser step consumes URL and field values from disk instead of re-parsing Gmail content.

## 1. Requirements & Constraints

- **REQ-001**: Add opt-in CLI form automation that uses links from `Email.links` returned by `GmailClient.fetch()` in `src/gmail_client.py`.
- **REQ-002**: Use the first HTTPS URL in `Email.links` by default; add CLI option `--link-index INDEX` in `src/main.py` to choose another extracted link by zero-based index.
- **REQ-003**: Add CLI option `--automate-form` in `src/main.py`; when this option is absent, the existing email fetch, console output, and export behavior must remain unchanged.
- **REQ-004**: Add CLI option `--form-config PATH` in `src/main.py`; default value must be `config/form_automation.json`.
- **REQ-005**: Add CLI option `--submit-form` in `src/main.py`; when this option is absent, automation must discover inputs and fill values but must not submit the form.
- **REQ-006**: Add CLI option `--automation-output PATH` in `src/main.py`; when provided, write structured JSON automation results to this file.
- **REQ-007**: Implement browser automation with Playwright for Python because it supports real browser rendering, locators, input filling, checkboxes, radio buttons, selects, clicks, auto-waiting, and headless execution.
- **REQ-008**: Discover all enabled page inputs matching `input`, `textarea`, `select`, and `[contenteditable="true"]` after navigating to the selected URL.
- **REQ-009**: Extract input metadata including `tag`, `type`, `name`, `id`, `label`, `placeholder`, `aria_label`, `required`, `disabled`, `visible`, and `options` for selects and radio groups.
- **REQ-010**: Fill text inputs, textareas, date/time inputs, number inputs, email inputs, telephone inputs, password inputs, and contenteditable fields with `locator.fill()`.
- **REQ-011**: Fill checkboxes and radio buttons with `locator.set_checked(True)` or `locator.check()`.
- **REQ-012**: Fill select elements with `locator.select_option(...)`.
- **REQ-013**: Submit the form only when `--submit-form` is present and the config defines a submit selector or the discovered form has exactly one submit control.
- **REQ-014**: Return one automation result per processed email containing `email_id`, `url`, `discovered_inputs`, `filled_fields`, `missing_required_fields`, `submitted`, `final_url`, and `status`.
- **REQ-015**: Print a concise terminal summary after automation: `Automated N URL form(s): S submitted, F filled without submit, E failed.`
- **REQ-016**: Add an optional `--invoice-code-output PATH` CLI option that writes a second JSON file containing `email_id`, `thread_id`, `subject`, `date`, selected `url`, extracted `invoice_code`, and `field_values`.
- **REQ-017**: Add an optional `--automation-input PATH` CLI option so form automation can consume URL and field values from an exported JSON handoff file.
- **REQ-018**: When `--invoice-code-output` and `--automate-form` are used together, form automation must use the newly written invoice-code JSON file as its input.
- **REQ-019**: Keep the existing direct in-memory automation path available when no JSON handoff file is provided.
- **SEC-001**: Require the config file to define `url_allowlist` as a non-empty list of hostnames; skip any extracted URL whose hostname is not allowlisted.
- **SEC-002**: Do not submit forms by default; submission requires explicit `--submit-form`.
- **SEC-003**: Do not log full filled values to terminal output; terminal summaries may include field names and masked values only.
- **SEC-004**: Do not write `config/form_automation.json` to git; add it to `.gitignore`.
- **SEC-005**: Do not widen Gmail OAuth scopes because this feature only reads email content and automates external web forms.
- **CON-001**: Preserve the existing flat `src/` import style; do not convert `src/` into a Python package.
- **CON-002**: Keep Gmail API access inside `src/gmail_client.py`; browser automation code must consume `Email` instances and must not call Gmail APIs directly.
- **CON-003**: Keep the initial implementation synchronous using `playwright.sync_api` to match the existing CLI flow.
- **PAT-001**: Follow the existing CLI pattern in `src/main.py`: argparse options, fetch emails once, then run optional post-fetch behavior.
- **PAT-002**: Follow the existing exporter pattern by isolating non-CLI logic in a dedicated module with focused unit tests.

## 2. Implementation Steps

### Implementation Phase 1

- GOAL-001: Add Playwright dependency, configuration contract, and safe defaults.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Add `playwright>=1.44.0` to `requirements.txt` below the existing third-party dependencies. | ✅ | 2026-06-03 |
| TASK-002 | Add `config/form_automation.example.json` with keys `url_allowlist`, `headless`, `timeout_ms`, `field_values`, `form_fields`, and `submit_selector`. | ✅ | 2026-06-03 |
| TASK-003 | Add `config/form_automation.json` to `.gitignore` because it may contain target-site field names, selectors, and sensitive mapping rules. | ✅ | 2026-06-03 |
| TASK-004 | Update `README.md` setup instructions with `python3 -m playwright install chromium` and `uv run python3 -m playwright install chromium` after dependency installation. | ✅ | 2026-06-03 |
| TASK-005 | Update `README.md` with an automation example: `python3 src/main.py "label:Petrolimex" --max 1 --automate-form --form-config config/form_automation.json --submit-form`. | ✅ | 2026-06-03 |

### Implementation Phase 2

- GOAL-002: Implement email-to-form value extraction and config loading.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-006 | Create `src/form_automation.py` and define dataclass `FieldValueRule` with fields `key: str`, `source: str`, `regex: str | None = None`, `group: int = 1`, and `default: str | None = None`. | ✅ | 2026-06-03 |
| TASK-007 | In `src/form_automation.py`, define dataclass `FormFieldRule` with fields `field_key: str`, `selector_strategy: str`, `selector_value: str`, `selector_name: str | None = None`, `input_type: str = "text"`, and `required: bool = True`. | ✅ | 2026-06-03 |
| TASK-008 | In `src/form_automation.py`, define dataclass `FormAutomationConfig` with fields `url_allowlist: list[str]`, `headless: bool`, `timeout_ms: int`, `field_values: list[FieldValueRule]`, `form_fields: list[FormFieldRule]`, and `submit_selector: dict | None`. | ✅ | 2026-06-03 |
| TASK-009 | Add function `load_form_automation_config(path: str) -> FormAutomationConfig` in `src/form_automation.py`; read UTF-8 JSON, validate required keys, validate `url_allowlist` is non-empty, and raise `ValueError` with actionable messages for invalid config. | ✅ | 2026-06-03 |
| TASK-010 | Add function `build_email_context(email: Email) -> dict[str, str]` in `src/form_automation.py`; include `id`, `thread_id`, `subject`, `sender`, `sender_email`, `date`, `snippet`, `body`, `links_joined`, and `first_link`. | ✅ | 2026-06-03 |
| TASK-011 | Add function `resolve_field_values(email: Email, config: FormAutomationConfig) -> dict[str, str]` in `src/form_automation.py`; for each `FieldValueRule`, read the configured context source and apply `regex` when present. | ✅ | 2026-06-03 |
| TASK-012 | In `resolve_field_values`, raise `ValueError` when a configured `source` is unknown or a required regex does not match and no default is configured. | ✅ | 2026-06-03 |

### Implementation Phase 3

- GOAL-003: Implement URL validation, browser navigation, input discovery, filling, and submission.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-013 | Add function `select_email_url(email: Email, link_index: int) -> str | None` in `src/form_automation.py`; return the selected HTTPS URL or `None` when the email has no usable URL. | ✅ | 2026-06-03 |
| TASK-014 | Add function `is_allowed_url(url: str, allowlist: list[str]) -> bool` in `src/form_automation.py`; parse the URL with `urllib.parse.urlparse` and allow exact hostname matches or subdomains of allowlisted hosts. | ✅ | 2026-06-03 |
| TASK-015 | Add dataclass `DiscoveredInput` in `src/form_automation.py` with fields `selector: str`, `tag: str`, `type: str`, `name: str`, `id: str`, `label: str`, `placeholder: str`, `aria_label: str`, `required: bool`, `disabled: bool`, `visible: bool`, and `options: list[str]`. | ✅ | 2026-06-03 |
| TASK-016 | Add function `discover_inputs(page) -> list[DiscoveredInput]` in `src/form_automation.py`; evaluate JavaScript over `input`, `textarea`, `select`, and `[contenteditable="true"]` elements and return deterministic metadata sorted by DOM order. | ✅ | 2026-06-03 |
| TASK-017 | Add function `locator_for_rule(page, rule: FormFieldRule)` in `src/form_automation.py`; support selector strategies `label`, `placeholder`, `name`, `id`, `css`, `role`, and `test_id`. | ✅ | 2026-06-03 |
| TASK-018 | Add function `fill_field(page, rule: FormFieldRule, value: str) -> None` in `src/form_automation.py`; route `text`, `textarea`, `date`, `time`, `number`, `email`, `tel`, `password`, and `contenteditable` to `fill`, `checkbox` and `radio` to `check`, and `select` to `select_option`. | ✅ | 2026-06-03 |
| TASK-019 | Add function `submit_page(page, submit_selector: dict | None) -> bool` in `src/form_automation.py`; click the configured submit locator when present, otherwise click the only visible `button[type=submit]`, `input[type=submit]`, or role button named with case-insensitive `submit|tra cứu|search|continue`. | ✅ | 2026-06-03 |
| TASK-020 | Add dataclass `FormAutomationResult` in `src/form_automation.py` with fields `email_id: str`, `url: str`, `discovered_inputs: list[dict]`, `filled_fields: list[str]`, `missing_required_fields: list[str]`, `submitted: bool`, `final_url: str`, `status: str`, and `error: str | None = None`. | ✅ | 2026-06-03 |
| TASK-021 | Add function `automate_email_form(email: Email, config: FormAutomationConfig, link_index: int, submit: bool) -> FormAutomationResult` in `src/form_automation.py`; open Chromium with `sync_playwright`, navigate to the selected allowed URL, discover inputs, resolve values, fill configured fields, optionally submit, and close the browser context in a `finally` block. | ✅ | 2026-06-03 |
| TASK-022 | Add function `automate_email_forms(emails: list[Email], config_path: str, link_index: int, submit: bool) -> list[FormAutomationResult]` in `src/form_automation.py`; load config once and call `automate_email_form` for each email. | ✅ | 2026-06-03 |

### Implementation Phase 4

- GOAL-004: Wire automation into the CLI and JSON result output.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-023 | Import `automate_email_forms` from `form_automation` in `src/main.py`. | ✅ | 2026-06-03 |
| TASK-024 | Add argparse option `--automate-form` with `action="store_true"` and help text `Open the selected extracted URL, fill configured form fields, and optionally submit.` | ✅ | 2026-06-03 |
| TASK-025 | Add argparse option `--form-config` with default `config/form_automation.json` and help text `Path to form automation JSON config.` | ✅ | 2026-06-03 |
| TASK-026 | Add argparse option `--link-index` with `type=int`, default `0`, and help text `Zero-based index into each email's extracted links.` | ✅ | 2026-06-03 |
| TASK-027 | Add argparse option `--submit-form` with `action="store_true"` and help text `Submit the form after filling fields.` | ✅ | 2026-06-03 |
| TASK-028 | Add argparse option `--automation-output` with `default=None` and help text `Write form automation results as JSON.` | ✅ | 2026-06-03 |
| TASK-029 | After optional email export in `src/main.py`, call `automate_email_forms(emails, args.form_config, args.link_index, args.submit_form)` only when `args.automate_form` is true. | ✅ | 2026-06-03 |
| TASK-030 | Add helper function `write_automation_results(results: list[FormAutomationResult], output_path: str) -> None` in `src/form_automation.py`; serialize dataclasses to UTF-8 JSON with `ensure_ascii=False` and `indent=2`. | ✅ | 2026-06-03 |
| TASK-031 | In `src/main.py`, when `args.automation_output` is provided and automation ran, call `write_automation_results(...)`. | ✅ | 2026-06-03 |
| TASK-032 | In `src/main.py`, after automation, print `Automated N URL form(s): S submitted, F filled without submit, E failed.` using counts from `FormAutomationResult.status`. | ✅ | 2026-06-03 |

### Implementation Phase 5

- GOAL-005: Add tests for config parsing, value extraction, URL safety, automation routing, and CLI wiring.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-033 | Create `tests/test_form_automation_config.py` covering valid config loading, missing `url_allowlist`, empty `url_allowlist`, unknown field value source, and regex extraction failures. | ✅ | 2026-06-03 |
| TASK-034 | Create `tests/test_form_automation_values.py` covering `build_email_context`, `sender_email` extraction from `From` headers, `first_link`, and `resolve_field_values` from `subject`, `snippet`, and `body`. | ✅ | 2026-06-03 |
| TASK-035 | Create `tests/test_form_automation_urls.py` covering HTTPS-only URL selection, `--link-index` behavior, allowlisted hostnames, subdomain allowlist behavior, and rejected external hostnames. | ✅ | 2026-06-03 |
| TASK-036 | Create `tests/test_form_automation_fill.py` using fake page and locator classes to verify `locator_for_rule`, `fill_field` routing for text, checkbox, radio, and select inputs, and `submit_page` configured-selector behavior without launching a real browser. | ✅ | 2026-06-03 |
| TASK-037 | Extend `tests/test_main.py` with a test that passes `--automate-form --form-config config/form_automation.json --link-index 0 --submit-form --automation-output results.json`, monkeypatches `main.automate_email_forms`, and asserts CLI arguments are forwarded correctly. | ✅ | 2026-06-03 |
| TASK-038 | Add one optional integration test file `tests/test_form_automation_playwright_integration.py` marked with `pytest.mark.playwright`; use a local static HTML form through `page.set_content(...)` and skip when Playwright browsers are unavailable. | ✅ | 2026-06-03 |
| TASK-039 | Run `python3 -m pytest` or `uv run python3 -m pytest` and confirm all non-integration tests pass. | ✅ | 2026-06-03 |
| TASK-040 | Run `python3 -m playwright install chromium` or `uv run python3 -m playwright install chromium`, then run `python3 -m pytest -m playwright` or `uv run python3 -m pytest -m playwright` and confirm the optional Playwright integration test passes. | ✅ | 2026-06-03 |

### Implementation Phase 6

- GOAL-006: Split extraction and automation with an explicit JSON handoff file.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-041 | Add `src/petrolimex.py` with reusable `extract_invoice_lookup_code(...)` so both export and automation use the same `Mã tra cứu` parser. | ✅ | 2026-06-04 |
| TASK-042 | Add exporter support for `--invoice-code-output`; write a JSON array containing email metadata, selected URL, `invoice_code`, and `field_values.invoice_code`. | ✅ | 2026-06-04 |
| TASK-043 | Add form automation input loading from the exported JSON handoff file. | ✅ | 2026-06-04 |
| TASK-044 | Add `--automation-input PATH` so automation can run from an existing JSON handoff without fetching Gmail again. | ✅ | 2026-06-04 |
| TASK-045 | When `--invoice-code-output` is provided with `--automate-form`, route automation through that JSON file instead of resolving values directly from `Email.body`. | ✅ | 2026-06-04 |
| TASK-046 | Update `README.md` to document the new three-step flow: full email JSON, invoice-code JSON, then form automation from JSON. | ✅ | 2026-06-04 |
| TASK-047 | Add focused tests for invoice-code JSON export, automation-input parsing, and CLI routing. | ✅ | 2026-06-04 |

## 3. Alternatives

- **ALT-001**: Use Selenium WebDriver. This was rejected for the first implementation because Playwright provides modern Python APIs, browser isolation, strong locators, and automatic actionability checks with less setup for this CLI workflow.
- **ALT-002**: Use `requests` plus Beautiful Soup to parse forms and submit HTTP POST requests. This was rejected because target pages may render inputs with JavaScript, require client-side events, or rely on browser navigation before submission.
- **ALT-003**: Hard-code field names for one target website in `src/main.py`. This was rejected because the extracted URLs and form fields can change; a JSON mapping keeps site-specific selectors outside application logic.
- **ALT-004**: Automatically submit every extracted link with no allowlist. This was rejected because external form submissions have side effects and require explicit user intent.

## 4. Dependencies

- **DEP-001**: Existing `Email` dataclass in `src/gmail_client.py`.
- **DEP-002**: Existing `Email.links` extraction implemented by `GmailClient._extract_links(...)`.
- **DEP-003**: Existing CLI flow in `src/main.py`.
- **DEP-004**: New runtime dependency `playwright>=1.44.0`.
- **DEP-005**: Chromium browser binaries installed by `python3 -m playwright install chromium` or `uv run python3 -m playwright install chromium`.
- **DEP-006**: Python standard library modules `json`, `dataclasses`, `re`, `urllib.parse`, and `pathlib`.
- **DEP-007**: Existing test dependency `pytest>=8.0.0`.

## 5. Files

- **FILE-001**: `requirements.txt` will add Playwright.
- **FILE-002**: `.gitignore` will ignore `config/form_automation.json`.
- **FILE-003**: `config/form_automation.example.json` will document the automation config schema.
- **FILE-004**: `src/form_automation.py` will implement config loading, email value extraction, URL validation, Playwright automation, and result serialization.
- **FILE-005**: `src/main.py` will add automation CLI flags and call the automation module after email fetching and optional export.
- **FILE-006**: `README.md` will document Playwright setup, config creation, dry-run fill behavior, and explicit submission behavior.
- **FILE-007**: `tests/test_form_automation_config.py` will cover config validation.
- **FILE-008**: `tests/test_form_automation_values.py` will cover email content value extraction.
- **FILE-009**: `tests/test_form_automation_urls.py` will cover URL selection and allowlist safety.
- **FILE-010**: `tests/test_form_automation_fill.py` will cover locator and field-fill routing without launching a browser.
- **FILE-011**: `tests/test_form_automation_playwright_integration.py` will cover one optional local Playwright fill-and-submit workflow.
- **FILE-012**: `tests/test_main.py` will be extended for CLI automation wiring.
- **FILE-013**: `src/petrolimex.py` will contain reusable Petrolimex invoice-code extraction.
- **FILE-014**: `src/exporter.py` will write the invoice-code JSON handoff file.

## 6. Testing

- **TEST-001**: Run `python3 -m pytest tests/test_form_automation_config.py` or `uv run python3 -m pytest tests/test_form_automation_config.py` and confirm config validation passes.
- **TEST-002**: Run `python3 -m pytest tests/test_form_automation_values.py` or `uv run python3 -m pytest tests/test_form_automation_values.py` and confirm email value extraction passes.
- **TEST-003**: Run `python3 -m pytest tests/test_form_automation_urls.py` or `uv run python3 -m pytest tests/test_form_automation_urls.py` and confirm URL selection and allowlist behavior passes.
- **TEST-004**: Run `python3 -m pytest tests/test_form_automation_fill.py` or `uv run python3 -m pytest tests/test_form_automation_fill.py` and confirm locator and fill routing passes.
- **TEST-005**: Run `python3 -m pytest tests/test_main.py` or `uv run python3 -m pytest tests/test_main.py` and confirm CLI automation wiring passes.
- **TEST-006**: Run `python3 -m pytest` or `uv run python3 -m pytest` and confirm the full non-integration suite passes.
- **TEST-007**: Run `python3 -m playwright install chromium` or `uv run python3 -m playwright install chromium`, then run `python3 -m pytest -m playwright` or `uv run python3 -m pytest -m playwright` and confirm optional browser integration passes.
- **TEST-008**: With valid Gmail credentials and a real `config/form_automation.json`, run `python3 src/main.py "label:Petrolimex" --max 1 --automate-form --automation-output /tmp/form-results.json` and confirm the target page opens headlessly, inputs are discovered, fields are filled, no submission occurs, and JSON results are written.
- **TEST-009**: With valid Gmail credentials and a real `config/form_automation.json`, run `python3 src/main.py "label:Petrolimex" --max 1 --automate-form --submit-form --automation-output /tmp/form-results.json` and confirm the form submits only for allowlisted URLs.
- **TEST-010**: Run `python3 -m pytest tests/test_exporter.py tests/test_form_automation_values.py tests/test_main.py` and confirm invoice-code JSON export, automation-input parsing, and CLI routing pass.
- **TEST-011**: With valid Gmail credentials and a real `config/form_automation.json`, run `python3 src/main.py "label:Petrolimex" --max 1 --output /tmp/emails.json --invoice-code-output /tmp/invoice-codes.json --automate-form --automation-output /tmp/form-results.json` and confirm automation consumes `/tmp/invoice-codes.json`.

## 7. Risks & Assumptions

- **RISK-001**: Target websites can change field labels, placeholders, names, IDs, or client-side validation rules; config-driven selectors reduce but do not remove this risk.
- **RISK-002**: Automatically submitting forms can create real external side effects; the implementation must require `--submit-form` and an allowlisted host.
- **RISK-003**: Some pages may require login, CAPTCHA, one-time tokens, bot detection bypass prevention, or user interaction; this plan does not bypass those controls.
- **RISK-004**: Email bodies can contain sensitive values; automation result output must be handled as sensitive data even when terminal logs mask values.
- **RISK-005**: Playwright browser binaries increase setup size and require an extra install command.
- **RISK-006**: The invoice-code JSON handoff file contains invoice lookup data and must be treated as sensitive local output.
- **ASSUMPTION-001**: The previous email link extraction feature provides the target URL in `Email.links`.
- **ASSUMPTION-002**: The first version can use a JSON mapping file for field-specific email value extraction and selector matching.
- **ASSUMPTION-003**: The target form is reachable in Chromium and does not require bypassing CAPTCHA, MFA, or access controls.
- **ASSUMPTION-004**: Processing emails sequentially is acceptable for the first version.
- **ASSUMPTION-005**: The JSON handoff file is the source of truth for automation when `--automation-input` or `--invoice-code-output` is provided.

## 8. Related Specifications / Further Reading

- [plan/feature-email-export-1.md](feature-email-export-1.md)
- [README.md](../README.md)
- [src/gmail_client.py](../src/gmail_client.py)
- [src/main.py](../src/main.py)
- [Playwright Python installation](https://playwright.dev/python/docs/intro)
- [Playwright Python actions and form input handling](https://playwright.dev/python/docs/input)
- [Playwright Python locators](https://playwright.dev/python/docs/locators)
- [Selenium Python waits documentation](https://selenium-python.readthedocs.io/waits.html)
