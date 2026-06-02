# Architecture

## 1) Architectural Style

- Primary style: small layered CLI.
- Why this classification: `src/main.py` owns command-line input/output, `src/gmail_client.py` wraps Gmail API operations and parsing, and `src/auth.py` owns OAuth credentials.
- Primary constraints: direct script execution depends on flat imports from `src/`; Gmail access requires OAuth credentials and read-only Gmail scope; message retrieval is network-bound through the official Gmail API.

## 2) System Flow

```text
src/main.py -> GmailClient.fetch() -> list_message_ids() -> get_email() -> Gmail API -> printed summaries
```

1. `src/main.py` loads `.env`, parses an optional Gmail query and `--max` value, and instantiates `GmailClient`.
2. `GmailClient.__init__` builds a Gmail API v1 service using credentials from `get_credentials()`.
3. `get_credentials()` loads `config/token.json` if present, refreshes expired credentials when possible, or starts the installed-app OAuth flow with `config/credentials.json`.
4. `GmailClient.fetch()` lists matching message IDs and fetches each message with `format="full"`.
5. `get_email()` normalizes Gmail headers into an `Email` dataclass and extracts a body from the MIME payload.
6. `src/main.py` prints date, sender, subject, and snippet for each fetched email.

## 3) Layer/Module Responsibilities

| Layer or module | Owns | Must not own | Evidence |
|-----------------|------|--------------|----------|
| CLI layer | Argument parsing, `.env` loading, terminal output | OAuth internals, Gmail API pagination | `src/main.py` |
| Auth layer | OAuth scope, credential file paths, token refresh and consent flow | Message parsing, query construction | `src/auth.py` |
| Gmail API wrapper | Gmail service setup, message listing, message fetching, MIME body extraction | CLI defaults, local credential file permissions | `src/gmail_client.py` |
| Local config files | User-provided OAuth client secret and generated token | Committed application logic | `README.md`, `.gitignore`, `src/auth.py` |

## 4) Reused Patterns

| Pattern | Where found | Why it exists |
|---------|-------------|---------------|
| Wrapper/client class | `GmailClient` in `src/gmail_client.py` | Keeps Gmail API calls behind a small application API: `list_message_ids`, `get_email`, and `fetch` |
| Dataclass DTO | `Email` in `src/gmail_client.py` | Normalizes Gmail response fields into a Python object for the CLI |
| Token cache | `TOKEN_FILE` handling in `src/auth.py` | Allows first run to be interactive and later runs to be headless |

## 5) Known Architectural Risks

- `fetch()` performs one API call per message after listing IDs, so large result sets scale linearly in network calls.
- The project is not packaged; imports rely on running `python src/main.py`, and a future test runner will need `src/` on `PYTHONPATH` or package setup.
- OAuth token storage is local-file based; README notes this should change for AWS/headless deployment.

## 6) Evidence

- `README.md`
- `CLAUDE.md`
- `.gitignore`
- `.env.example`
- `src/main.py`
- `src/auth.py`
- `src/gmail_client.py`
