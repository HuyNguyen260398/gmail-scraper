# Gmail Automation

Reads emails from Gmail by label / search query using the official Gmail API (OAuth2, read-only scope).

## Project layout

```
gmail-scraper/
├── src/
│   ├── auth.py           # OAuth2 flow + token caching
│   ├── exporter.py       # JSON / text export helpers
│   ├── petrolimex.py     # Petrolimex email value parsing
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

   Using `python3` and `pip`:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python3 -m playwright install chromium
   ```

   Or using `uv`:
   ```bash
   uv venv .venv && source .venv/bin/activate
   uv pip install -r requirements.txt
   uv run python3 -m playwright install chromium
   ```

4. **Configure (optional)**
   ```bash
   cp .env.example .env
   # edit GMAIL_QUERY / GMAIL_MAX_RESULTS
   ```

5. **Run**

   Using `python3`:
   ```bash
   python3 src/main.py "label:Petrolimex"
   ```

   Or using `uv`:
   ```bash
   uv run python3 src/main.py "label:Petrolimex"
   ```

   First run opens a browser for consent and writes `config/token.json`.
   Subsequent runs are headless. Terminal output includes message metadata, snippet, extracted links, and the full extracted body.

## Exporting email content

Save fetched messages to an output file with `--output`. JSON is the default format:

```bash
python3 src/main.py "label:Petrolimex" --max 10 --output emails.json
```

Or using `uv`:

```bash
uv run python3 src/main.py "label:Petrolimex" --max 10 --output emails.json
```

Use `--format text` for a readable plain-text export:

```bash
python3 src/main.py "label:Petrolimex is:unread" --max 5 --output emails.txt --format text
```

Or using `uv`:

```bash
uv run python3 src/main.py "label:Petrolimex is:unread" --max 5 --output emails.txt --format text
```

Each JSON item includes `id`, `thread_id`, `subject`, `sender`, `date`, `snippet`, `body`, `labels`, and `links`.

For Petrolimex form automation, also write a smaller JSON handoff file that contains the selected URL and extracted `Mã tra cứu` value:

```bash
python3 src/main.py "label:Petrolimex" --max 1 --output tmp/emails.json --invoice-code-output tmp/invoice-codes.json
```

Each invoice-code JSON item includes `email_id`, `thread_id`, `subject`, `date`, `url`, `invoice_code`, and `field_values`. The `field_values` object is what form automation uses to fill configured page fields, for example `{"invoice_code": "FN2V8BMAG*"}`.

## Automating extracted URL forms

Form automation is opt-in. The preferred flow is JSON-first: fetch Gmail content, write the full email JSON, write the derived invoice-code JSON, then run automation from that derived JSON. Automation opens the selected HTTPS URL in Chromium, discovers form inputs, fills configured fields from the JSON `field_values`, and submits only when `--submit-form` is provided.

The checked-in example targets the Petrolimex invoice-code form. It fills `Mã tra cứu HĐ` from email text like `Mã tra cứu: FN2V8BMAG*`. The website-generated captcha fields, `Mã xác thực` and `Nhập mã xác thực`, remain manual.

Create a local config from the example:

```bash
cp config/form_automation.example.json config/form_automation.json
```

Dry-run fill without submitting:

```bash
python3 src/main.py "label:Petrolimex" --max 1 --output tmp/emails.json --invoice-code-output tmp/invoice-codes.json
python3 src/main.py --automate-form --automation-input tmp/invoice-codes.json --form-config config/form_automation.json --automation-output tmp/form-results.json
```

Submit the form after filling and manual captcha entry:

```bash
python3 src/main.py --automate-form --automation-input tmp/invoice-codes.json --form-config config/form_automation.json --submit-form
```

You can also fetch, write both JSON files, and automate in one command. In that mode, automation reads the file passed to `--invoice-code-output`:

```bash
python3 src/main.py "label:Petrolimex" --max 1 --output tmp/emails.json --invoice-code-output tmp/invoice-codes.json --automate-form --form-config config/form_automation.json --automation-output tmp/form-results.json
```

Or using `uv`:

```bash
uv run python3 src/main.py "label:Petrolimex" --max 1 --output tmp/emails.json --invoice-code-output tmp/invoice-codes.json
uv run python3 src/main.py --automate-form --automation-input tmp/invoice-codes.json --form-config config/form_automation.json --automation-output tmp/form-results.json
uv run python3 src/main.py --automate-form --automation-input tmp/invoice-codes.json --form-config config/form_automation.json --submit-form
```

For Petrolimex, Chromium opens visibly even if the config has `headless` set differently. After `Mã tra cứu HĐ` is filled, type the captcha shown beside `Mã xác thực` into `Nhập mã xác thực`, then press Enter in the terminal to continue. Without `--submit-form`, the browser is left filled but not submitted.

`config/form_automation.json` is gitignored because selectors and field mapping rules may contain sensitive site-specific data. Treat `tmp/emails.json`, `tmp/invoice-codes.json`, and `tmp/form-results.json` as sensitive local artifacts because they can contain invoice data. The config must include a non-empty `url_allowlist`; URLs outside those hostnames are skipped.

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
