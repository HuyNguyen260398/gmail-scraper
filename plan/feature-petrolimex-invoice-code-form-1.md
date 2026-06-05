---
goal: Fill Petrolimex invoice-code lookup form from Gmail email content
version: 1.2
date_created: 2026-06-03
last_updated: 2026-06-05
owner: Repository maintainers
status: 'Blocked on third-party CAPTCHA bypass'
tags: [feature, gmail, petrolimex, browser-automation, captcha]
---

# Introduction

![Status: Blocked](https://img.shields.io/badge/status-Blocked-red)

This plan updates the existing form automation flow so the CLI can open the Petrolimex electronic invoice lookup page, fill the `Mã tra cứu HĐ` field from Gmail email content, and support the required captcha step without attempting to bypass it. The sample source text is `assets/sample-email-content.txt`, where the required invoice lookup value appears as `Mã tra cứu: FN2V8BMAG*`.

## Research Update: Captcha Handling

The selected solution is not full CAPTCHA solving. CAPTCHA is an access-control mechanism, so this project will not use OCR, trained models, browser-fingerprint workarounds, or third-party solving services to bypass it.

The practical Python solution is human-in-the-loop automation:

1. Playwright fills all non-CAPTCHA fields from the exported JSON handoff.
2. Playwright captures the CAPTCHA image element to a local file using an element screenshot.
3. The CLI prompts the user to read that image or the visible browser window and type the CAPTCHA value.
4. Playwright fills the configured CAPTCHA input with the user-provided text.
5. If `--submit-form` is present, Playwright clicks the configured submit selector.

This uses normal Playwright primitives: `locator.screenshot(...)` for element capture, `locator.fill(...)` for text inputs, and headed mode or `page.pause()` only when manual inspection is needed.

## Blocked Point: Full CAPTCHA Autofill

Full zero-touch CAPTCHA autofill for the Petrolimex public site is blocked. The requested behavior would require bypassing or defeating a third-party anti-automation control. This project must not implement or document OCR-based solving, trained CAPTCHA recognition, browser-fingerprint evasion, token replay, CAPTCHA farm integrations, or third-party solver APIs for that purpose.

This block affects only the CAPTCHA step. The rest of the automation remains valid:

- Gmail extraction can run unattended.
- Full email JSON and invoice-code JSON handoff files can be generated unattended.
- Browser automation can open the URL and fill `Mã tra cứu HĐ` unattended.
- Submission can be automated after a supported CAPTCHA path is available.

Unblocking requires one of the compliant alternatives listed below, preferably an official Petrolimex integration or an authorized no-CAPTCHA environment.

## 1. Requirements & Constraints

- **REQ-001**: Target the Petrolimex invoice-code lookup URL `https://hoadon.petrolimex.com.vn/SearchInvoicebycode/Index`.
- **REQ-002**: Use the existing `Email.body` value produced by `GmailClient._extract_body(...)` in `src/gmail_client.py` as the source for invoice-code extraction.
- **REQ-003**: Extract invoice lookup code text from Vietnamese email content matching `Mã tra cứu: FN2V8BMAG*` in `assets/sample-email-content.txt` line 11.
- **REQ-004**: Preserve the trailing `*` in extracted invoice lookup codes because the sample email content includes it as part of the lookup value.
- **REQ-005**: Fill the Petrolimex invoice-code input `Mã tra cứu HĐ` using DOM field `id="strFkey"` and `name="strFkey"`.
- **REQ-006**: Treat `Mã xác thực` as the captcha image label and `Nhập mã xác thực` as the captcha text input.
- **REQ-007**: Do not attempt to solve, OCR, bypass, or auto-fill the captcha from the page image.
- **REQ-008**: Support a manual captcha flow that keeps the browser open after filling `strFkey`, lets the user enter captcha text into DOM field `id="captch"` and `name="captch"`, and then submits only after explicit user action or explicit CLI submission mode.
- **REQ-009**: Keep current `--automate-form` behavior available for generic forms; Petrolimex-specific behavior must be opt-in through config and/or a focused CLI flag.
- **REQ-010**: Update `config/form_automation.example.json` so it contains a working Petrolimex invoice-code example instead of the current generic portal example.
- **REQ-011**: Add config support for a CAPTCHA image selector, for example `captcha_image_selector`, using the same selector strategy pattern as form fields.
- **REQ-012**: Add config support for a local CAPTCHA screenshot output directory, defaulting to `tmp/captcha`.
- **REQ-013**: When a manual CAPTCHA field is present, capture the CAPTCHA image element screenshot before prompting the user.
- **REQ-014**: Prompt the user for the CAPTCHA text in the terminal and fill the configured CAPTCHA input with the typed value.
- **REQ-015**: Never persist the user-entered CAPTCHA value in automation result JSON.
- **REQ-016**: If the CAPTCHA image selector is missing or cannot be captured, fall back to the current headed-browser manual entry flow.
- **REQ-017**: Full CAPTCHA autofill remains out of scope unless Petrolimex provides an official API, integration contract, or documented machine-access path that removes the need to bypass CAPTCHA.
- **SEC-001**: Keep `config/form_automation.json` gitignored because it can contain local operational choices.
- **SEC-002**: Keep URL allowlisting mandatory; Petrolimex automation must allow only `hoadon.petrolimex.com.vn`.
- **SEC-003**: Do not log the full extracted invoice lookup code to terminal output unless the user explicitly asks for verbose diagnostics.
- **SEC-004**: Do not widen Gmail OAuth scopes because this update only reads email content.
- **CON-001**: Preserve the flat `src/` import style used by `src/main.py`.
- **CON-002**: Preserve synchronous Playwright usage in `src/form_automation.py`.
- **CON-003**: Do not introduce external OCR, captcha-solving, or anti-bot dependencies.
- **PAT-001**: Extend the existing dataclass and JSON config pattern in `src/form_automation.py` lines 13-39 instead of adding hard-coded Petrolimex logic inside `src/main.py`.
- **PAT-002**: Continue routing CLI orchestration through `src/main.py` lines 46-97 and keep field extraction/filling logic inside `src/form_automation.py`.

## 2. Implementation Steps

### Implementation Phase 1

- GOAL-001: Make Petrolimex invoice-code extraction deterministic and test-covered.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Add function `extract_invoice_lookup_code(text: str) -> str | None` to `src/form_automation.py` after `build_email_context(...)`; use regex `r"Mã\s+tra\s+cứu\s*:\s*([^\s\r\n]+)"` with `re.IGNORECASE` and return the stripped first capture group. | ✅ | 2026-06-03 |
| TASK-002 | Update `resolve_field_values(...)` in `src/form_automation.py` lines 141-170 to support a new `FieldValueRule.source` value `petrolimex_invoice_code`; when this source is used, call `extract_invoice_lookup_code(email.body)` instead of reading a direct context key. | ✅ | 2026-06-03 |
| TASK-003 | When `petrolimex_invoice_code` extraction returns `None` and no rule default exists, raise `ValueError("Petrolimex invoice lookup code not found in email body.")`. | ✅ | 2026-06-03 |
| TASK-004 | Add `tests/test_petrolimex_invoice_code.py` with a fixture that reads `assets/sample-email-content.txt` using `Path(...).read_text(encoding="utf-8")` and asserts `extract_invoice_lookup_code(...) == "FN2V8BMAG*"`. | ✅ | 2026-06-03 |
| TASK-005 | In `tests/test_petrolimex_invoice_code.py`, add a `resolve_field_values(...)` test using an `Email` whose `body` is the sample file content and a config rule `{"key": "invoice_code", "source": "petrolimex_invoice_code"}`. | ✅ | 2026-06-03 |

### Implementation Phase 2

- GOAL-002: Add manual captcha handling to the existing automation flow.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-006 | Add field `manual_after_fill: bool` to `FormAutomationConfig` in `src/form_automation.py` lines 32-39 with default value `False`. | ✅ | 2026-06-03 |
| TASK-007 | Update `load_form_automation_config(...)` in `src/form_automation.py` lines 89-121 to read `manual_after_fill` from JSON with `bool(raw.get("manual_after_fill", False))`. | ✅ | 2026-06-03 |
| TASK-008 | Add field `requires_manual_input: bool = False` to `FormFieldRule` in `src/form_automation.py` lines 22-29. | ✅ | 2026-06-03 |
| TASK-009 | Update `_load_form_field_rules(...)` in `src/form_automation.py` lines 420-446 to read `requires_manual_input` from each form field rule with default `False`. | ✅ | 2026-06-03 |
| TASK-010 | Update `automate_email_form(...)` in `src/form_automation.py` lines 304-372 so fields marked `requires_manual_input=True` are not considered missing when no email-derived value exists. | ✅ | 2026-06-03 |
| TASK-011 | Add helper function `wait_for_manual_completion(page, config: FormAutomationConfig, submit: bool) -> bool` in `src/form_automation.py`; it must print concise instructions, call Python `input("Press Enter after entering captcha in the browser...")`, and call `submit_page(...)` only when `submit` is `True`. | ✅ | 2026-06-03 |
| TASK-012 | Update `automate_email_form(...)` so when `config.manual_after_fill` is `True`, Chromium launches with `headless=False` regardless of the config `headless` value, fills configured non-manual fields, waits for manual captcha completion, then records status `submitted` when submission occurs or `filled` when no submission is requested. | ✅ | 2026-06-03 |

### Implementation Phase 3

- GOAL-003: Provide a working Petrolimex config example.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-013 | Replace `config/form_automation.example.json` with a Petrolimex invoice-code example containing `url_allowlist: ["hoadon.petrolimex.com.vn"]`, `headless: false`, `manual_after_fill: true`, and `timeout_ms: 30000`. | ✅ | 2026-06-03 |
| TASK-014 | In `config/form_automation.example.json`, set `field_values` to one rule: `{"key": "invoice_code", "source": "petrolimex_invoice_code"}`. | ✅ | 2026-06-03 |
| TASK-015 | In `config/form_automation.example.json`, set `form_fields` rule for invoice code to `{"field_key": "invoice_code", "selector_strategy": "id", "selector_value": "strFkey", "input_type": "text", "required": true}`. | ✅ | 2026-06-03 |
| TASK-016 | In `config/form_automation.example.json`, add a captcha field rule `{"field_key": "captcha", "selector_strategy": "id", "selector_value": "captch", "input_type": "text", "required": true, "requires_manual_input": true}`. | ✅ | 2026-06-03 |
| TASK-017 | In `config/form_automation.example.json`, set `submit_selector` to `{"selector_strategy": "css", "selector_value": "#SearchformByfkey input[type=\"submit\"]"}` so submission targets the invoice-code tab form only. | ✅ | 2026-06-03 |

### Implementation Phase 4

- GOAL-004: Update CLI and documentation for the Petrolimex manual captcha workflow.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-018 | Update `src/main.py` help text for `--submit-form` on lines 62-66 to state that captcha-protected forms require user captcha entry before submission. | ✅ | 2026-06-03 |
| TASK-019 | Update `README.md` with a Petrolimex example command: `python3 src/main.py "label:Petrolimex" --max 1 --automate-form --form-config config/form_automation.json --submit-form`. | ✅ | 2026-06-03 |
| TASK-020 | Update `README.md` to instruct users to copy `config/form_automation.example.json` to `config/form_automation.json`, keep the browser window open, type the captcha shown beside `Mã xác thực`, then press Enter in the terminal to continue. | ✅ | 2026-06-03 |
| TASK-021 | Update `README.md` to document that `Mã tra cứu HĐ` is filled from email text like `Mã tra cứu: FN2V8BMAG*`, while `Nhập mã xác thực` is manual because the captcha is generated by the website. | ✅ | 2026-06-03 |

### Implementation Phase 5

- GOAL-005: Verify unit behavior and preserve existing automation behavior.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-022 | Update `tests/test_form_automation_config.py` to assert `manual_after_fill` defaults to `False` when omitted and loads as `True` when present. | ✅ | 2026-06-03 |
| TASK-023 | Update `tests/test_form_automation_config.py` to assert `requires_manual_input` defaults to `False` and loads as `True` for the captcha rule. | ✅ | 2026-06-03 |
| TASK-024 | Update `tests/test_form_automation_fill.py` or add a new fake-page unit test proving that a required manual captcha field without a resolved email value does not add `captcha` to `missing_required_fields`. | ✅ | 2026-06-03 |
| TASK-025 | Run `python3 -m pytest tests/test_petrolimex_invoice_code.py tests/test_form_automation_config.py tests/test_form_automation_values.py tests/test_form_automation_fill.py`. | ✅ | 2026-06-03 |
| TASK-026 | Run `python3 -m pytest` and confirm the full existing test suite passes. | ✅ | 2026-06-03 |

### Implementation Phase 6

- GOAL-006: Improve CAPTCHA handling with a human-in-the-loop screenshot and terminal prompt.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-027 | Add a dataclass for optional manual CAPTCHA config, including `image_selector_strategy`, `image_selector_value`, `input_field_key`, and `screenshot_dir`. | ⬜ | |
| TASK-028 | Update `load_form_automation_config(...)` to parse the optional CAPTCHA config and default `screenshot_dir` to `tmp/captcha`. | ⬜ | |
| TASK-029 | Add helper `capture_manual_captcha(page, config, email_id) -> str | None` that locates the CAPTCHA image and writes an element screenshot path such as `tmp/captcha/msg-1-captcha.png`. | ⬜ | |
| TASK-030 | Add helper `prompt_for_manual_field(field_label: str, screenshot_path: str | None) -> str` that asks the user for the CAPTCHA value without logging it elsewhere. | ⬜ | |
| TASK-031 | Update `wait_for_manual_completion(...)` so it captures the CAPTCHA image, prompts for user text, fills the `requires_manual_input=True` CAPTCHA input, and only then optionally submits. | ⬜ | |
| TASK-032 | Update `config/form_automation.example.json` with the Petrolimex CAPTCHA image selector once confirmed from the live page. | ⬜ | |
| TASK-033 | Update README instructions to show the new `tmp/captcha/...png` screenshot path and terminal prompt behavior. | ⬜ | |
| TASK-034 | Add unit tests proving manual CAPTCHA fields are filled from prompted text and the prompted value is not written to `FormAutomationResult`. | ⬜ | |
| TASK-035 | Add a fake-page test proving CAPTCHA screenshot capture uses the configured selector and gracefully falls back when capture fails. | ⬜ | |

## 3. Alternatives

- **ALT-001**: Hard-code Petrolimex selectors and regex directly in `src/main.py`. This is rejected because `src/main.py` should remain CLI orchestration only, and the existing config-based automation module already owns selectors and field extraction.
- **ALT-002**: Use OCR or an external captcha-solving service for `Mã xác thực`. This is rejected because captcha is an access-control mechanism and the project should not bypass it.
- **ALT-003**: Require the captcha value to come from email content. This is rejected because the sample email content contains `Mã tra cứu`, `Mẫu số`, `Ký hiệu`, and `Số hóa đơn`, but it does not contain the website captcha value.
- **ALT-004**: Use the invoice-detail tab with `MST người bán`, `Ký hiệu hóa đơn`, and `Số hóa đơn`. This is rejected for this update because the user explicitly chose the invoice-code form with `Mã tra cứu HĐ`.
- **ALT-005**: Use `page.pause()` as the main user workflow. This is useful for debugging and remains a fallback, but a terminal prompt plus CAPTCHA element screenshot is faster and easier to test.
- **ALT-006**: Request an official Petrolimex invoice lookup API or partner integration. This is the preferred path for true unattended automation because it avoids browser scraping and CAPTCHA bypass entirely.
- **ALT-007**: Ask Petrolimex for an allowlisted account, API key, service credential, or server-to-server workflow for authorized automated invoice lookup.
- **ALT-008**: Use a test or staging environment owned by the project where CAPTCHA is disabled by configuration. This is acceptable only for environments controlled by the project or explicitly authorized by the site owner.
- **ALT-009**: Split the workflow into a queue: run extraction and form prefill automatically, then mark records as `requires_manual_captcha` for later human completion. This preserves reliable unattended extraction while making the CAPTCHA block explicit.
- **ALT-010**: If Petrolimex emails include enough invoice metadata, avoid the CAPTCHA page and export the email-derived invoice details directly for downstream processing.

## 4. Dependencies

- **DEP-001**: Existing `Email` dataclass in `src/gmail_client.py`.
- **DEP-002**: Existing `Email.body` extraction in `GmailClient._extract_body(...)`.
- **DEP-003**: Existing `src/form_automation.py` Playwright-based automation module.
- **DEP-004**: Existing `config/form_automation.example.json` config convention.
- **DEP-005**: Existing `assets/sample-email-content.txt` sample fixture.
- **DEP-006**: Runtime dependency `playwright` already listed in `requirements.txt`.
- **DEP-007**: Test dependency `pytest` already used by the repo.
- **DEP-008**: Playwright `locator.screenshot(...)` for CAPTCHA element capture.
- **DEP-009**: Existing Playwright `locator.fill(...)` behavior for entering the user-provided CAPTCHA text.

## 5. Files

- **FILE-001**: `src/form_automation.py` will add Petrolimex invoice-code extraction, manual captcha config fields, and manual completion flow.
- **FILE-002**: `config/form_automation.example.json` will become a Petrolimex-focused invoice-code form example.
- **FILE-003**: `src/main.py` will update CLI help text for captcha-protected submission behavior.
- **FILE-004**: `README.md` will document the Petrolimex command and manual captcha workflow.
- **FILE-005**: `tests/test_petrolimex_invoice_code.py` will cover sample email extraction and config-based field value resolution.
- **FILE-006**: `tests/test_form_automation_config.py` will cover the new config fields.
- **FILE-007**: `tests/test_form_automation_fill.py` will cover required manual field handling.
- **FILE-008**: `src/form_automation.py` will add CAPTCHA screenshot capture, prompt handling, and manual field filling.
- **FILE-009**: `config/form_automation.example.json` will document the Petrolimex CAPTCHA image selector and screenshot directory.
- **FILE-010**: `tests/test_form_automation_fill.py` will cover screenshot capture and prompt-to-fill behavior.

## 6. Testing

- **TEST-001**: `python3 -m pytest tests/test_petrolimex_invoice_code.py` must pass and prove the sample email body extracts `FN2V8BMAG*`.
- **TEST-002**: `python3 -m pytest tests/test_form_automation_config.py` must pass and prove `manual_after_fill` and `requires_manual_input` config values are validated and loaded.
- **TEST-003**: `python3 -m pytest tests/test_form_automation_fill.py` must pass and prove non-manual fields still route through `fill_field(...)`.
- **TEST-004**: `python3 -m pytest tests/test_main.py` must pass and prove existing CLI automation wiring is not broken.
- **TEST-005**: `python3 -m pytest` must pass for the complete test suite.
- **TEST-006**: Manual verification command `python3 src/main.py "label:Petrolimex" --max 1 --automate-form --form-config config/form_automation.json` must open the Petrolimex page, fill `Mã tra cứu HĐ`, leave captcha for manual entry, and avoid submission when `--submit-form` is absent.
- **TEST-007**: Manual verification command `python3 src/main.py "label:Petrolimex" --max 1 --automate-form --form-config config/form_automation.json --submit-form` must open the Petrolimex page, fill `Mã tra cứu HĐ`, wait for user captcha entry, then submit after terminal confirmation.
- **TEST-008**: `python3 -m pytest tests/test_form_automation_config.py tests/test_form_automation_fill.py` must pass after adding CAPTCHA screenshot config and prompt behavior.
- **TEST-009**: Manual verification with real Petrolimex page must create a CAPTCHA image under `tmp/captcha`, fill `id="captch"` from terminal input, and submit only when `--submit-form` is present.

## 7. Risks & Assumptions

- **RISK-001**: Petrolimex can change DOM IDs `strFkey`, `captch`, or form ID `SearchformByfkey`; the JSON config keeps selectors adjustable without code changes.
- **RISK-002**: Petrolimex can reject automation or require additional user interaction; this plan does not bypass website protections.
- **RISK-003**: Running with `manual_after_fill` requires an interactive terminal because the implementation waits for `input(...)`.
- **RISK-004**: Processing multiple emails with manual captcha enabled will require one captcha interaction per email.
- **RISK-005**: Petrolimex may render the CAPTCHA image through a selector that changes, requires reload, or is not directly screenshot-friendly; the implementation must fall back to visible browser entry.
- **RISK-006**: CAPTCHA screenshots in `tmp/captcha` are short-lived operational artifacts and should be treated as sensitive local files.
- **RISK-007**: The project cannot meet a strict zero-touch browser-submission requirement while Petrolimex requires a CAPTCHA and no official automation path is available.
- **ASSUMPTION-001**: Email bodies continue to include a line shaped like `Mã tra cứu: <code>`.
- **ASSUMPTION-002**: The `*` character in the sample lookup code is intentional and must be preserved.
- **ASSUMPTION-003**: The selected email link points to `https://hoadon.petrolimex.com.vn` or the config can direct the automation to the fixed Petrolimex lookup URL in a later follow-up.
- **ASSUMPTION-004**: It is acceptable for the first Petrolimex-specific flow to require visible Chromium instead of headless mode.
- **ASSUMPTION-005**: The user is available to read and type the CAPTCHA value during each automation run.
- **ASSUMPTION-006**: If full unattended operation is required, the project owner will obtain an authorized non-CAPTCHA integration path from Petrolimex or another official source.

## 8. Related Specifications / Further Reading

- [Existing generic URL form automation plan](feature-url-form-automation-1.md)
- [Sample Petrolimex email content](../assets/sample-email-content.txt)
- [Form automation module](../src/form_automation.py)
- [CLI entry point](../src/main.py)
- [Petrolimex invoice lookup page](https://hoadon.petrolimex.com.vn/SearchInvoicebycode/Index)
- [Playwright Python screenshots](https://playwright.dev/python/docs/screenshots)
- [Playwright Python locator screenshot API](https://playwright.dev/python/docs/api/class-locator#locator-screenshot)
- [Playwright Python input actions](https://playwright.dev/python/docs/input)
- [Playwright Python page pause API](https://playwright.dev/python/docs/api/class-page#page-pause)
