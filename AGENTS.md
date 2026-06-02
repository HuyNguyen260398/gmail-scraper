# Repository Guidelines

## Project Structure & Module Organization

This is a small Python CLI project for reading Gmail messages through the official Gmail API.

- `src/main.py` is the command-line entry point.
- `src/auth.py` handles OAuth2, token refresh, and local token caching.
- `src/gmail_client.py` wraps Gmail message listing, fetching, and parsing.
- `src/exporter.py` serializes fetched emails to JSON or plain text files.
- `config/` stores local Gmail OAuth files. `credentials.json` is user-provided, and `token.json` is generated on first consent; both are gitignored.
- `tests/` contains pytest coverage for exporter behavior and CLI export wiring.
- `docs/codebase/` contains generated architecture, structure, testing, and convention notes.

## Build, Test, and Development Commands

Create and activate a local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Or using `uv`:

```bash
uv venv .venv
source .venv/bin/activate
```

Install runtime dependencies:

```bash
pip install -r requirements.txt
```

Or using `uv`:

```bash
uv pip install -r requirements.txt
```

Run the CLI with the default `.env` query or an explicit Gmail search query:

```bash
python3 src/main.py
python3 src/main.py "label:Petrolimex is:unread" --max 10
python3 src/main.py "label:Petrolimex" --output emails.json --format json
```

Or using `uv`:

```bash
uv run python3 src/main.py
uv run python3 src/main.py "label:Petrolimex is:unread" --max 10
uv run python3 src/main.py "label:Petrolimex" --output emails.json --format json
```

Run tests:

```bash
python3 -m pytest
```

Or using `uv`:

```bash
uv run python3 -m pytest
```

There is no build step, package script, or lint command configured yet.

## Coding Style & Naming Conventions

Use Python `snake_case` for files, functions, and methods. Use `PascalCase` for classes such as `GmailClient` and `Email`. Use uppercase for constants and environment variables, for example `SCOPES`, `GMAIL_QUERY`, and `GMAIL_MAX_RESULTS`.

Keep imports grouped as standard library, third-party packages, then local modules. The current code uses flat local imports from `src/`, not package-relative imports. No formatter is configured, so keep formatting close to the existing style: 4-space indentation and concise docstrings for public functions.

## Testing Guidelines

The project uses `pytest`. Place tests under `tests/` and use names such as `tests/test_gmail_client.py` or `tests/test_exporter.py`. Unit tests should mock Gmail API calls and avoid reading real `config/token.json` or `config/credentials.json`. Add integration tests only when credentials and secret handling are explicit.

## Commit & Pull Request Guidelines

Recent commits use short, lowercase subject lines such as `init commit` and `renamed app`. Keep commit messages brief and imperative when possible, for example `add gmail client tests`.

Pull requests should include a concise summary, setup or verification commands run, and any Gmail API or credential-handling impact. Link related issues when available. Include screenshots only for user-visible output changes where terminal output is relevant.

## Security & Configuration Tips

Never commit `.env`, `config/credentials.json`, or `config/token.json`. The Gmail scope is currently read-only; widen it only when the feature requires modifying, sending, or deleting mail.
