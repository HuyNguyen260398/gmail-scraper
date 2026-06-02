# External Integrations

## 1) Integration Inventory

| System | Type (API/DB/Queue/etc) | Purpose | Auth model | Criticality | Evidence |
|--------|---------------------------|---------|------------|-------------|----------|
| Gmail API | API | List and read Gmail messages matching a search query | OAuth2 installed-app flow with read-only Gmail scope | High | `README.md`, `src/auth.py`, `src/gmail_client.py` |
| Google Cloud OAuth client | Auth configuration | Supplies desktop-app client credentials for Gmail consent flow | User-provided `config/credentials.json` | High | `README.md`, `src/auth.py` |
| Local `.env` file | Runtime config | Optional CLI defaults for query and max results | Local file loaded by `python-dotenv`; no secret requirement shown | Low | `.env.example`, `src/main.py` |

## 2) Data Stores

| Store | Role | Access layer | Key risk | Evidence |
|-------|------|--------------|----------|----------|
| `config/token.json` | Local OAuth token cache generated on first successful auth | `src/auth.py` | Sensitive refresh token material on local disk | `src/auth.py`, `.gitignore`, `README.md` |
| Gmail mailbox | Remote source of email message data | `src/gmail_client.py` | API failures, quota limits, or auth failures stop fetches | `src/gmail_client.py`, `requirements.txt` |

No application database, cache, queue, or object store is configured in the repository.

## 3) Secrets and Credentials Handling

- Credential sources: `config/credentials.json` for OAuth client credentials; `config/token.json` for generated user token; optional `.env` for non-secret CLI defaults.
- Hardcoding checks: Gmail OAuth scope and default query are hardcoded in source; secrets are not hardcoded in the inspected files.
- Rotation or lifecycle notes: changing `SCOPES` requires deleting `config/token.json` so consent runs again, per `CLAUDE.md`.

## 4) Reliability and Failure Behavior

- Retry/backoff behavior: `[TODO]` no explicit retry policy is implemented around Gmail API calls.
- Timeout policy: `[TODO]` no explicit timeout configuration is present in the Gmail client setup.
- Circuit-breaker or fallback behavior: none found.

## 5) Observability for Integrations

- Logging around external calls: no logging around OAuth or Gmail API calls.
- Metrics/tracing coverage: none found.
- Missing visibility gaps: no structured logs for query, page count, API failure type, token refresh, or fetch latency.

## 6) Evidence

- `README.md`
- `CLAUDE.md`
- `.env.example`
- `.gitignore`
- `requirements.txt`
- `src/main.py`
- `src/auth.py`
- `src/gmail_client.py`
- `docs/codebase/.codebase-scan.txt`
