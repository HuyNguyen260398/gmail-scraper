---
goal: Implement email content export to JSON or text files
version: 1.0
date_created: 2026-06-02
last_updated: 2026-06-02
owner: Repository maintainers
status: 'Completed'
tags: [feature, cli, export, gmail]
---

# Introduction

![Status: Completed](https://img.shields.io/badge/status-Completed-brightgreen)

This plan defines the implementation steps for adding file export support to the Gmail scraper CLI. The feature will fetch Gmail messages using the existing `GmailClient.fetch()` flow and save parsed email content to either JSON or plain text output files.

## 1. Requirements & Constraints

- **REQ-001**: Add a CLI option `--output PATH` in `src/main.py` that writes fetched email content to the specified file.
- **REQ-002**: Add a CLI option `--format json|text` in `src/main.py`; default value must be `json`.
- **REQ-003**: JSON output must include `id`, `thread_id`, `subject`, `sender`, `date`, `snippet`, `body`, `labels`, and `links` for each email.
- **REQ-004**: Text output must include readable per-email sections containing date, sender, subject, labels, snippet, links, and body.
- **REQ-005**: The existing console summary behavior must remain available after fetching emails.
- **SEC-001**: Do not write or expose `config/credentials.json`, `config/token.json`, or OAuth secrets in exported files.
- **CON-001**: Use only Python standard library modules for export serialization.
- **CON-002**: Preserve the existing flat `src/` import style.
- **PAT-001**: Keep Gmail API access inside `src/gmail_client.py`; export formatting must not call Gmail APIs directly.

## 2. Implementation Steps

### Implementation Phase 1

- GOAL-001: Add export serialization functions with no Gmail API dependency.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Create `src/exporter.py` with function `email_to_dict(email: Email) -> dict` that maps every `Email` dataclass field to JSON-serializable values. | ✅ | 2026-06-02 |
| TASK-002 | Add function `write_json(emails: list[Email], output_path: str) -> None` in `src/exporter.py`; use `json.dump(..., ensure_ascii=False, indent=2)` and write UTF-8 text. | ✅ | 2026-06-02 |
| TASK-003 | Add function `write_text(emails: list[Email], output_path: str) -> None` in `src/exporter.py`; write deterministic plain-text sections separated by a line of 80 `=` characters. | ✅ | 2026-06-02 |
| TASK-004 | Add function `write_emails(emails: list[Email], output_path: str, output_format: str) -> None` in `src/exporter.py`; route `json` to `write_json`, `text` to `write_text`, and raise `ValueError` for unsupported formats. | ✅ | 2026-06-02 |

### Implementation Phase 2

- GOAL-002: Wire export support into the command-line interface.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-005 | Update `src/main.py` usage docstring to include `python3 src/main.py "label:Petrolimex" --max 10 --output emails.json --format json`; repository docs also list `uv run python3 src/main.py ...` as a second option. | ✅ | 2026-06-02 |
| TASK-006 | Import `write_emails` from `exporter` in `src/main.py`. | ✅ | 2026-06-02 |
| TASK-007 | Add argparse option `--output` with `default=None` and help text `Write fetched emails to this file path.` | ✅ | 2026-06-02 |
| TASK-008 | Add argparse option `--format` with `choices=["json", "text"]`, `default="json"`, and help text `Output file format when --output is provided.` | ✅ | 2026-06-02 |
| TASK-009 | After `client.fetch(...)`, call `write_emails(emails, args.output, args.format)` only when `args.output` is not empty. | ✅ | 2026-06-02 |
| TASK-010 | After writing an output file, print `Saved N message(s) to PATH as FORMAT.` where `N`, `PATH`, and `FORMAT` are actual runtime values. | ✅ | 2026-06-02 |

### Implementation Phase 3

- GOAL-003: Add focused tests and documentation for export behavior.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-011 | Add `pytest` to `requirements.txt` because the repository currently has no test framework configured. | ✅ | 2026-06-02 |
| TASK-012 | Create `tests/test_exporter.py` with unit tests for `email_to_dict`, `write_json`, `write_text`, and invalid `write_emails` format handling. | ✅ | 2026-06-02 |
| TASK-013 | Ensure tests construct `Email` instances directly and do not import or instantiate `GmailClient`. | ✅ | 2026-06-02 |
| TASK-014 | Update `README.md` setup or run section with JSON and text export examples. | ✅ | 2026-06-02 |
| TASK-015 | Update `AGENTS.md` testing guidance to include `pytest`, command `python3 -m pytest`, and `uv run python3 -m pytest` as a second option. | ✅ | 2026-06-02 |

## 3. Alternatives

- **ALT-001**: Put export logic directly in `src/main.py`. This was rejected because serialization logic is easier to test in a dedicated module.
- **ALT-002**: Add separate flags `--json-output` and `--text-output`. This was rejected because one `--output` path plus `--format` is simpler and scales to future formats.
- **ALT-003**: Export only JSON in the first version. This was rejected because the requested feature explicitly mentioned JSON or text files and text support is low complexity.

## 4. Dependencies

- **DEP-001**: Existing `Email` dataclass in `src/gmail_client.py`.
- **DEP-002**: Existing `GmailClient.fetch(query: str, max_results: int) -> list[Email]` method.
- **DEP-003**: Python standard library `json` and `pathlib`.
- **DEP-004**: `pytest` for repository tests after `requirements.txt` is updated.

## 5. Files

- **FILE-001**: `src/exporter.py` will be added for export serialization and file writing.
- **FILE-002**: `src/main.py` will be updated with CLI options and export invocation.
- **FILE-003**: `tests/test_exporter.py` will be added for unit coverage.
- **FILE-004**: `requirements.txt` will be updated with `pytest`.
- **FILE-005**: `README.md` will document export usage.
- **FILE-006**: `AGENTS.md` will document the new test command.

## 6. Testing

- **TEST-001**: Run `python3 -m pytest tests/test_exporter.py` or `uv run python3 -m pytest tests/test_exporter.py` and confirm all exporter unit tests pass.
- **TEST-002**: Run `python3 -m pytest` or `uv run python3 -m pytest` and confirm the full test suite passes.
- **TEST-003**: Manually run `python3 src/main.py "label:Petrolimex" --max 1 --output /tmp/gmail-export.json --format json` or `uv run python3 src/main.py "label:Petrolimex" --max 1 --output /tmp/gmail-export.json --format json` with valid credentials and confirm a JSON array is written.
- **TEST-004**: Manually run `python3 src/main.py "label:Petrolimex" --max 1 --output /tmp/gmail-export.txt --format text` or `uv run python3 src/main.py "label:Petrolimex" --max 1 --output /tmp/gmail-export.txt --format text` with valid credentials and confirm readable text sections are written.

## 7. Risks & Assumptions

- **RISK-001**: Exported email bodies may contain sensitive content; users must choose safe output paths and avoid committing generated exports.
- **RISK-002**: Large email bodies or high `--max` values may create large output files.
- **RISK-003**: Manual CLI verification requires valid Gmail OAuth configuration in `config/credentials.json` and may open a browser on first run.
- **ASSUMPTION-001**: `GmailClient.fetch()` already returns the email body in `Email.body`.
- **ASSUMPTION-002**: The first implementation does not need streaming output; writing the fetched list after completion is acceptable.
- **ASSUMPTION-003**: The output directory must already exist; automatic parent directory creation is not required for this version.

## 8. Related Specifications / Further Reading

- [README.md](../README.md)
- [AGENTS.md](../AGENTS.md)
- [docs/codebase/ARCHITECTURE.md](../docs/codebase/ARCHITECTURE.md)
- [docs/codebase/TESTING.md](../docs/codebase/TESTING.md)
