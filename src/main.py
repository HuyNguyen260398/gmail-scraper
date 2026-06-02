"""Entry point: read emails from a given Gmail label / query.

Usage:
    python src/main.py                          # default query from .env or "label:Petrolimex"
    python src/main.py "label:Petrolimex is:unread"
    python src/main.py "from:billing@example.com newer_than:30d" --max 10
"""

import argparse
import os

from dotenv import load_dotenv

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
    args = parser.parse_args()

    client = GmailClient()
    emails = client.fetch(query=args.query, max_results=args.max)

    print(f"Found {len(emails)} message(s) for query: {args.query!r}\n")
    for i, email in enumerate(emails, 1):
        print(f"[{i}] {email.date}")
        print(f"    From:    {email.sender}")
        print(f"    Subject: {email.subject}")
        print(f"    Snippet: {email.snippet[:120]}")
        print()


if __name__ == "__main__":
    main()
