# Coding Conventions

## 1) Naming Rules

| Item | Rule | Example | Evidence |
|------|------|---------|----------|
| Files | Python `snake_case` | `gmail_client.py` | `src/gmail_client.py` |
| Functions/methods | Python `snake_case`; private helpers use leading underscore | `get_credentials`, `_extract_body` | `src/auth.py`, `src/gmail_client.py` |
| Types/interfaces | Python class names use `PascalCase` | `GmailClient`, `Email` | `src/gmail_client.py` |
| Constants/env vars | Module constants and env vars use uppercase | `SCOPES`, `TOKEN_FILE`, `GMAIL_QUERY` | `src/auth.py`, `.env.example`, `src/main.py` |

## 2) Formatting and Linting

- Formatter: `[TODO]` no formatter config found.
- Linter: `[TODO]` no linter config found.
- Most relevant enforced rules: `[TODO]` no repository-enforced rules found.
- Run commands: `[TODO]` no lint/format commands documented.

## 3) Import and Module Conventions

- Import grouping/order: standard library imports first, third-party imports second, local imports last, as seen in all source files.
- Alias vs relative import policy: flat local imports from `src/`, not package-relative imports.
- Public exports/barrel policy: no package `__init__.py` or export barrel exists.

## 4) Error and Logging Conventions

- Error strategy by layer: `src/auth.py` raises `FileNotFoundError` when `config/credentials.json` is missing; Gmail API failures are not caught locally and will propagate from the Google client.
- Logging style and required context fields: no logging library or structured logging convention is configured.
- Sensitive-data redaction rules: secrets are excluded by `.gitignore`; no runtime redaction policy is implemented.

## 5) Testing Conventions

- Test file naming/location rule: tests live under `tests/` and use `test_*.py` names.
- Mocking strategy norm: pytest monkeypatch is used for CLI dependency isolation.
- Coverage expectation: `[TODO]` no coverage tool or threshold is configured.

## 6) Evidence

- `CLAUDE.md`
- `.gitignore`
- `.env.example`
- `src/main.py`
- `src/auth.py`
- `src/gmail_client.py`
- `docs/codebase/.codebase-scan.txt`
