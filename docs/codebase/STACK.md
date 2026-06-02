# Technology Stack

## 1) Runtime Summary

| Area | Value | Evidence |
|------|-------|----------|
| Primary language | Python | `src/main.py`, `src/auth.py`, `src/gmail_client.py` |
| Runtime + version | Python, exact version not pinned in repository | `README.md`, `CLAUDE.md`, `requirements.txt` |
| Package manager | `pip` with `requirements.txt` | `README.md`, `CLAUDE.md`, `requirements.txt` |
| Module/build system | Direct script execution; no installable package, no build step | `README.md`, `CLAUDE.md`, `src/main.py` |

## 2) Production Frameworks and Dependencies

| Dependency | Version | Role in system | Evidence |
|------------|---------|----------------|----------|
| `google-api-python-client` | `>=2.120.0` | Builds the Gmail API service client | `requirements.txt`, `src/gmail_client.py` |
| `google-auth` | `>=2.29.0` | Credential object and token refresh support | `requirements.txt`, `src/auth.py` |
| `google-auth-oauthlib` | `>=1.2.0` | Installed-app OAuth2 consent flow | `requirements.txt`, `src/auth.py` |
| `google-auth-httplib2` | `>=0.2.0` | Google API client auth transport dependency | `requirements.txt` |
| `python-dotenv` | `>=1.0.0` | Loads `.env` values for CLI defaults | `requirements.txt`, `src/main.py` |

## 3) Development Toolchain

| Tool | Purpose | Evidence |
|------|---------|----------|
| `[TODO]` | No linter, formatter, build tool, or test framework is configured | `CLAUDE.md`, `docs/codebase/.codebase-scan.txt` |

## 4) Key Commands

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
python src/main.py "label:Petrolimex is:unread" --max 10
```

There is no documented build, test, or lint command.

## 5) Environment and Config

- Config sources: `.env.example`, `config/credentials.json`, `config/token.json`.
- Required env vars: none required for startup; optional `GMAIL_QUERY` and `GMAIL_MAX_RESULTS` control CLI defaults.
- Deployment/runtime constraints: first local run requires interactive OAuth browser consent unless a valid token file already exists; README notes AWS deployments should not ship `config/token.json`.

## 6) Evidence

- `requirements.txt`
- `.env.example`
- `.gitignore`
- `README.md`
- `CLAUDE.md`
- `src/main.py`
- `src/auth.py`
- `src/gmail_client.py`
- `docs/codebase/.codebase-scan.txt`
