# Gmail Automation

Reads emails from Gmail by label / search query using the official Gmail API (OAuth2, read-only scope).

## Project layout

```
gmail-scraper/
├── src/
│   ├── auth.py           # OAuth2 flow + token caching
│   ├── exporter.py       # JSON / text export helpers
│   ├── gmail_client.py   # list / get / parse messages
│   └── main.py           # CLI entry point
├── config/
│   ├── credentials.json  # YOU provide (gitignored)
│   └── token.json        # auto-generated on first run (gitignored)
├── tests/
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

1. **Create a Google Cloud project & enable the Gmail API**
   - Go to <https://console.cloud.google.com/>
   - Create a project → APIs & Services → Library → enable **Gmail API**.

2. **Create OAuth credentials**
   - APIs & Services → Credentials → Create Credentials → **OAuth client ID**.
   - Application type: **Desktop app**.
   - Download the JSON and save it as `config/credentials.json`.
   - Under OAuth consent screen, add your Google account as a **test user**.

3. **Install dependencies**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure (optional)**
   ```bash
   cp .env.example .env
   # edit GMAIL_QUERY / GMAIL_MAX_RESULTS
   ```

5. **Run**
   ```bash
   python src/main.py "label:Petrolimex"
   ```
   First run opens a browser for consent and writes `config/token.json`.
   Subsequent runs are headless.

## Exporting email content

Save fetched messages to an output file with `--output`. JSON is the default format:

```bash
python src/main.py "label:Petrolimex" --max 10 --output emails.json
```

Use `--format text` for a readable plain-text export:

```bash
python src/main.py "label:Petrolimex is:unread" --max 5 --output emails.txt --format text
```

Each JSON item includes `id`, `thread_id`, `subject`, `sender`, `date`, `snippet`, `body`, and `labels`.

## Gmail search syntax (the `query` arg)

| Example | Meaning |
|---|---|
| `label:Petrolimex` | all mail under that label |
| `label:Petrolimex is:unread` | unread only |
| `label:Petrolimex newer_than:7d` | last 7 days |
| `from:billing@example.com` | by sender |

## Notes for AWS deployment

- Don't ship `token.json` in code. Store the refresh token in **Secrets Manager** or **SSM Parameter Store** and load it at runtime.
- For a Google **Workspace** org account, prefer a **service account with domain-wide delegation** — no interactive consent, ideal for headless Lambda/EventBridge jobs.
- For incremental sync, track `historyId` and use `users.history.list` instead of re-scanning.
- For near-real-time, use Gmail `watch` → Pub/Sub push notifications.
