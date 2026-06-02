"""File export helpers for fetched Gmail messages."""

import json
from pathlib import Path

from gmail_client import Email


def email_to_dict(email: Email) -> dict:
    """Return a JSON-serializable dictionary for an Email."""
    return {
        "id": email.id,
        "thread_id": email.thread_id,
        "subject": email.subject,
        "sender": email.sender,
        "date": email.date,
        "snippet": email.snippet,
        "body": email.body,
        "labels": list(email.labels),
    }


def write_json(emails: list[Email], output_path: str) -> None:
    """Write emails as an indented UTF-8 JSON array."""
    data = [email_to_dict(email) for email in emails]
    with Path(output_path).open("w", encoding="utf-8") as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=2)


def write_text(emails: list[Email], output_path: str) -> None:
    """Write emails as readable plain text sections."""
    separator = "=" * 80
    sections = []

    for index, email in enumerate(emails, 1):
        labels = ", ".join(email.labels) if email.labels else "(none)"
        sections.append(
            "\n".join(
                [
                    f"Email {index}",
                    separator,
                    f"Date: {email.date}",
                    f"From: {email.sender}",
                    f"Subject: {email.subject}",
                    f"Labels: {labels}",
                    f"Snippet: {email.snippet}",
                    "",
                    "Body:",
                    email.body,
                ]
            )
        )

    Path(output_path).write_text("\n\n".join(sections), encoding="utf-8")


def write_emails(emails: list[Email], output_path: str, output_format: str) -> None:
    """Write emails to output_path using the requested output format."""
    if output_format == "json":
        write_json(emails, output_path)
        return
    if output_format == "text":
        write_text(emails, output_path)
        return

    raise ValueError(f"Unsupported output format: {output_format}")
