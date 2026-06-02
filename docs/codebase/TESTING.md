# Testing Patterns

## 1) Test Stack and Commands

- Primary test framework: `pytest`.
- Assertion/mocking tools: pytest assertions and monkeypatch.
- Commands:

```bash
python3 -m pytest
uv run python3 -m pytest

python3 -m pytest tests/test_exporter.py
uv run python3 -m pytest tests/test_exporter.py

# [TODO] no coverage command is documented
```

## 2) Test Layout

- Test file placement pattern: tests live under `tests/`.
- Naming convention: `test_*.py`, for example `tests/test_exporter.py` and `tests/test_gmail_client.py`.
- Setup files and where they run: tests currently add `src/` to `sys.path` in each file.

## 3) Test Scope Matrix

| Scope | Covered? | Typical target | Notes |
|-------|----------|----------------|-------|
| Unit | Partial | `exporter` helpers, `GmailClient._extract_body`, `GmailClient._extract_links`, CLI export wiring | Auth and pagination are not covered |
| Integration | No | Gmail API OAuth and fetch flow | No test files or integration config exist |
| E2E | No | CLI command `python3 src/main.py ...` or `uv run python3 src/main.py ...` | No E2E runner or command exists |

## 4) Mocking and Isolation Strategy

- Main mocking approach: monkeypatch direct dependencies, such as replacing `main.GmailClient`.
- Isolation guarantees: exporter tests use `tmp_path` and do not touch local Gmail credential files.
- Common failure mode in tests: import path friction because the project is not packaged.

## 5) Coverage and Quality Signals

- Coverage tool + threshold: `[TODO]` none configured.
- Current reported coverage: `[TODO]` no coverage report exists.
- Known gaps/flaky areas: Gmail API, OAuth behavior, and pagination are untested in repository.

## 6) Evidence

- `CLAUDE.md`
- `tests/`
- `tests/test_exporter.py`
- `tests/test_gmail_client.py`
- `tests/test_main.py`
- `src/auth.py`
- `src/gmail_client.py`
- `src/main.py`
- `docs/codebase/.codebase-scan.txt`
