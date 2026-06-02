# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup with python3 and pip
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Or setup with uv
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt

# Run with python3 (query is optional; defaults to GMAIL_QUERY env or "label:Petrolimex")
python3 src/main.py
python3 src/main.py "label:Petrolimex is:unread" --max 10

# Or run with uv
uv run python3 src/main.py
uv run python3 src/main.py "label:Petrolimex is:unread" --max 10
```

First run opens a browser for OAuth consent and writes `config/token.json`; later runs are headless.

Run tests with `python3 -m pytest` or `uv run python3 -m pytest`. There is no build step or linter configured.

## Architecture

A small CLI that reads Gmail messages via the official Gmail API. Flow:

`main.py` (arg parsing) → `GmailClient` → `auth.get_credentials()`

- **`src/auth.py`** — OAuth2 with read-only scope (`gmail.readonly`). Caches a refresh token at `config/token.json` and auto-refreshes it. The OAuth client secret must be placed manually at `config/credentials.json` (Desktop-app type, downloaded from Google Cloud Console). Both files are gitignored.
- **`src/gmail_client.py`** — `GmailClient.fetch(query, max_results)` is the main API: it lists message IDs (Gmail search syntax, paginated 100/page) then fetches each into an `Email` dataclass. `_extract_body` walks the MIME tree, preferring `text/plain` and falling back to `text/html`.
- **`src/main.py`** — CLI entry point; prints a summary per message.

### Things to know before editing

- **Flat imports.** Modules in `src/` import each other without a package prefix (`from gmail_client import GmailClient`, `from auth import get_credentials`). This works because scripts are run directly as `python3 src/main.py` or `uv run python3 src/main.py`, which puts `src/` on `sys.path`. There is no `__init__.py` / installable package. New modules should follow the same flat style, and tests add `src/` to `sys.path`.
- **Changing the OAuth scope** (in `auth.py SCOPES`) requires deleting `config/token.json` so the consent flow re-runs — an existing token will not gain new permissions.

### Deployment notes (from README)

For AWS/headless use: store the refresh token in Secrets Manager / SSM instead of `token.json`; for Workspace orgs prefer a service account with domain-wide delegation; for sync use `historyId` + `users.history.list`, or Gmail `watch` → Pub/Sub for near-real-time.
