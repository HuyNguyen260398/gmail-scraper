"""File export helpers for fetched Gmail messages."""

import json
from pathlib import Path
from urllib.parse import urlparse

from gmail_client import Email
from petrolimex import extract_invoice_lookup_code


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
        "links": list(email.links),
    }


def write_json(emails: list[Email], output_path: str) -> None:
    """Write emails as an indented UTF-8 JSON array."""
    data = [email_to_dict(email) for email in emails]
    with Path(output_path).open("w", encoding="utf-8") as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=2)


def invoice_lookup_to_dict(email: Email, link_index: int = 0) -> dict:
    """Return the extracted Petrolimex lookup code and selected URL for automation."""
    invoice_code = extract_invoice_lookup_code(email.body)
    return {
        "email_id": email.id,
        "thread_id": email.thread_id,
        "subject": email.subject,
        "date": email.date,
        "url": _select_https_url(email.links, link_index) or "",
        "invoice_code": invoice_code or "",
        "field_values": {"invoice_code": invoice_code} if invoice_code else {},
    }


def write_invoice_lookup_codes(
    emails: list[Email], output_path: str, link_index: int = 0
) -> None:
    """Write extracted Petrolimex lookup codes as an automation-ready JSON array."""
    data = [invoice_lookup_to_dict(email, link_index) for email in emails]
    with Path(output_path).open("w", encoding="utf-8") as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=2)


def write_text(emails: list[Email], output_path: str) -> None:
    """Write emails as readable plain text sections."""
    separator = "=" * 80
    sections = []

    for index, email in enumerate(emails, 1):
        labels = ", ".join(email.labels) if email.labels else "(none)"
        links = "\n".join(email.links) if email.links else "(none)"
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
                    "Links:",
                    links,
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


def _select_https_url(links: list[str], link_index: int) -> str | None:
    if link_index < 0:
        return None

    https_links = [
        link for link in links if urlparse(link).scheme.lower() == "https"
    ]
    if link_index >= len(https_links):
        return None
    return https_links[link_index]
