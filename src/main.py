"""Entry point: read emails from a given Gmail label / query.

Usage:
    python3 src/main.py                          # default query from .env or "label:Petrolimex"
    python3 src/main.py "label:Petrolimex is:unread"
    python3 src/main.py "from:billing@example.com newer_than:30d" --max 10
    python3 src/main.py "label:Petrolimex" --max 10 --output emails.json --format json
    python3 src/main.py "label:Petrolimex" --max 1 --automate-form
"""

import argparse
import os

from dotenv import load_dotenv

from exporter import write_emails
from form_automation import automate_email_forms, write_automation_results
from gmail_client import GmailClient

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Read Gmail messages by query.")
    parser.add_argument(
        "query",
        nargs="?",
        default=os.getenv("GMAIL_QUERY", "label:Petrolimex"),
        help="Gmail search query (default from GMAIL_QUERY env or 'label:Petrolimex').",
    )
    parser.add_argument(
        "--max", type=int, default=int(os.getenv("GMAIL_MAX_RESULTS", "20")),
        help="Maximum number of messages to fetch.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write fetched emails to this file path.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output file format when --output is provided.",
    )
    parser.add_argument(
        "--automate-form",
        action="store_true",
        help="Open the selected extracted URL, fill configured form fields, and optionally submit.",
    )
    parser.add_argument(
        "--form-config",
        default="config/form_automation.json",
        help="Path to form automation JSON config.",
    )
    parser.add_argument(
        "--link-index",
        type=int,
        default=0,
        help="Zero-based index into each email's extracted links.",
    )
    parser.add_argument(
        "--submit-form",
        action="store_true",
        help=(
            "Submit the form after filling fields. Captcha-protected forms "
            "require user captcha entry before submission."
        ),
    )
    parser.add_argument(
        "--automation-output",
        default=None,
        help="Write form automation results as JSON.",
    )
    args = parser.parse_args()

    client = GmailClient()
    emails = client.fetch(query=args.query, max_results=args.max)

    if args.output:
        write_emails(emails, args.output, args.format)
        print(f"Saved {len(emails)} message(s) to {args.output} as {args.format}.")

    if args.automate_form:
        automation_results = automate_email_forms(
            emails,
            args.form_config,
            args.link_index,
            args.submit_form,
        )
        if args.automation_output:
            write_automation_results(automation_results, args.automation_output)
        submitted = sum(1 for result in automation_results if result.status == "submitted")
        filled = sum(1 for result in automation_results if result.status == "filled")
        failed = sum(1 for result in automation_results if result.status == "failed")
        print(
            "Automated "
            f"{len(automation_results)} URL form(s): "
            f"{submitted} submitted, {filled} filled without submit, {failed} failed."
        )

    print(f"Found {len(emails)} message(s) for query: {args.query!r}\n")
    for i, email in enumerate(emails, 1):
        print(f"[{i}] {email.date}")
        print(f"    From:    {email.sender}")
        print(f"    Subject: {email.subject}")
        print(f"    Snippet: {email.snippet[:120]}")
        print("    Links:")
        if email.links:
            for link in email.links:
                print(f"        {link}")
        else:
            print("        (none)")
        print("    Body:")
        print(email.body or "    (no body)")
        print()


if __name__ == "__main__":
    main()
