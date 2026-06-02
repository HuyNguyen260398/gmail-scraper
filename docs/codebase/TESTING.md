# Testing Patterns

## 1) Test Stack and Commands

- Primary test framework: `[TODO]` none configured.
- Assertion/mocking tools: `[TODO]` none configured.
- Commands:

```bash
# [TODO] no test command is documented
# [TODO] no unit test command is documented
# [TODO] no integration/e2e test command is documented
# [TODO] no coverage command is documented
```

## 2) Test Layout

- Test file placement pattern: `tests/` exists as a top-level directory.
- Naming convention: `[TODO]` no test files exist to establish a naming convention.
- Setup files and where they run: `[TODO]` no test setup files exist.

## 3) Test Scope Matrix

| Scope | Covered? | Typical target | Notes |
|-------|----------|----------------|-------|
| Unit | No | `auth.get_credentials`, `GmailClient._extract_body`, `GmailClient.list_message_ids` | No test files exist |
| Integration | No | Gmail API OAuth and fetch flow | No test files or integration config exist |
| E2E | No | CLI command `python src/main.py ...` | No E2E runner or command exists |

## 4) Mocking and Isolation Strategy

- Main mocking approach: `[TODO]` no mocking approach is present.
- Isolation guarantees: `[TODO]` no tests exist to show cleanup or reset behavior.
- Common failure mode in tests: `[TODO]` cannot be determined without tests.

## 5) Coverage and Quality Signals

- Coverage tool + threshold: `[TODO]` none configured.
- Current reported coverage: `[TODO]` no coverage report exists.
- Known gaps/flaky areas: empty `tests/` directory; Gmail API and OAuth behavior are untested in repository.

## 6) Evidence

- `CLAUDE.md`
- `tests/`
- `src/auth.py`
- `src/gmail_client.py`
- `src/main.py`
- `docs/codebase/.codebase-scan.txt`
