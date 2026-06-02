# Codebase Concerns

## 1) Top Risks (Prioritized)

| Severity | Concern | Evidence | Impact | Suggested action |
|----------|---------|----------|--------|------------------|
| High | No configured tests for OAuth, Gmail API pagination, MIME parsing, or CLI behavior | `CLAUDE.md`, `tests/`, `src/gmail_client.py` | Regressions can break authentication or message parsing without detection | Add focused unit tests for MIME extraction and pagination using mocked Gmail service objects |
| Medium | Local token-file credential storage is unsuitable for the AWS/headless deployment noted in README | `README.md`, `src/auth.py`, `.gitignore` | Shipping or mishandling refresh tokens would create credential exposure risk | Abstract token loading/storage before AWS deployment and use Secrets Manager or SSM as README suggests |
| Medium | Message fetching is sequential: list IDs, then fetch each message one at a time | `src/gmail_client.py` | Large result sets can be slow and quota-sensitive | Consider batch requests, concurrency with limits, or incremental sync using `historyId` |
| Medium | No explicit retry, timeout, logging, or metrics around Gmail API calls | `src/gmail_client.py`, `docs/codebase/.codebase-scan.txt` | Failures are harder to diagnose and may abort the whole run | Add bounded retry/timeout policy and structured logging around list/get calls |
| Low | Project is not packaged; imports depend on direct script execution from `src/main.py` | `CLAUDE.md`, `src/main.py`, `src/gmail_client.py` | Tests and alternate entry points need path setup | Add package metadata or document `PYTHONPATH=src` for tests |

## 2) Technical Debt

| Debt item | Why it exists | Where | Risk if ignored | Suggested fix |
|-----------|---------------|-------|-----------------|---------------|
| Missing test harness | The repo has a placeholder `tests/` directory but no test framework or files | `tests/`, `CLAUDE.md` | Fragile changes to auth and parsing | Add `pytest` and unit tests for pure parsing logic first |
| No lint/format configuration | Scan found no formatter/linter config | `docs/codebase/.codebase-scan.txt` | Style can drift as files are added | Add `ruff` or another Python formatter/linter if desired |
| Flat import layout | Running `python src/main.py` works, but package boundaries are not formalized | `CLAUDE.md`, `src/main.py`, `src/gmail_client.py` | Test/import friction as project grows | Convert `src/` into an installable package or set a documented test path |

## 3) Security Concerns

| Risk | OWASP category (if applicable) | Evidence | Current mitigation | Gap |
|------|--------------------------------|----------|--------------------|-----|
| OAuth refresh token stored locally | N/A | `src/auth.py`, `.gitignore` | `config/token.json` is gitignored and chmodded to `0600` after write | No secret manager abstraction for deployment |
| OAuth client secret expected in local config file | N/A | `README.md`, `src/auth.py`, `.gitignore` | `config/credentials.json` is gitignored | No validation of file permissions for `credentials.json` |
| Email content may be printed or processed locally | N/A | `src/main.py`, `src/gmail_client.py` | CLI prints only date/from/subject/snippet, not full body | No logging/redaction policy if output expands later |

## 4) Performance and Scaling Concerns

| Concern | Evidence | Current symptom | Scaling risk | Suggested improvement |
|---------|----------|-----------------|-------------|-----------------------|
| One `get` request per message | `src/gmail_client.py` | Acceptable for small `--max` values | Slow runs and quota pressure for larger result sets | Batch, parallelize with limits, or use incremental sync |
| Full message format fetched for every email | `src/gmail_client.py` | Needed for body extraction | More payload than needed if only summaries are printed | Fetch metadata when body is not needed |
| No incremental sync state | `README.md`, `src/gmail_client.py` | Each run searches current mailbox query | Re-scanning grows with mailbox size | Track `historyId` and use `users.history.list` |

## 5) Fragile/High-Churn Areas

| Area | Why fragile | Churn signal | Safe change strategy |
|------|-------------|-------------|----------------------|
| `src/auth.py` | Touches OAuth scopes, token refresh, local secret files, and interactive browser flow | No Git history available; scan reports no commits | Test with mocked credentials and document scope-change token invalidation |
| `src/gmail_client.py` | Handles Gmail pagination, remote calls, and recursive MIME parsing | No Git history available; largest source file in scan output | Add unit tests for pagination and nested MIME payloads before broad changes |
| `src/main.py` | User-facing CLI defaults and output | No Git history available | Keep CLI behavior covered by a small subprocess or parser-level test |

## 6) `[ASK USER]` Questions

1. [ASK USER] Should this remain a local-only CLI, or should the next target be AWS/headless deployment as described in the README?
2. [ASK USER] Should the app eventually read email bodies for downstream automation, or is summary output the intended product surface?
3. [ASK USER] Should this project be converted into an installable Python package before adding tests and more modules?

## 7) Evidence

- `README.md`
- `CLAUDE.md`
- `.gitignore`
- `requirements.txt`
- `src/main.py`
- `src/auth.py`
- `src/gmail_client.py`
- `tests/`
- `docs/codebase/.codebase-scan.txt`
