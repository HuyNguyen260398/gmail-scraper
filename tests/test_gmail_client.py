import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gmail_client import GmailClient


def encoded(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii").rstrip("=")


def test_extract_body_collects_all_plain_text_parts_in_order():
    payload = {
        "mimeType": "multipart/mixed",
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {"data": encoded("first section")},
            },
            {
                "mimeType": "multipart/related",
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": encoded("second section")},
                    },
                    {
                        "mimeType": "image/png",
                        "body": {"attachmentId": "image-1"},
                    },
                ],
            },
        ],
    }

    assert GmailClient._extract_body(payload) == "first section\n\nsecond section"


def test_extract_body_skips_text_attachments():
    payload = {
        "mimeType": "multipart/mixed",
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {"data": encoded("message body")},
            },
            {
                "mimeType": "text/plain",
                "filename": "notes.txt",
                "headers": [
                    {"name": "Content-Disposition", "value": "attachment"}
                ],
                "body": {"data": encoded("attachment body")},
            },
        ],
    }

    assert GmailClient._extract_body(payload) == "message body"


def test_extract_body_falls_back_to_readable_html_text():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {
                "mimeType": "text/html",
                "body": {
                    "data": encoded(
                        "<html><body><p>Hello&nbsp;there</p>"
                        "<div>Total: <strong>123</strong></div>"
                        "<style>.hidden{display:none}</style></body></html>"
                    )
                },
            },
        ],
    }

    assert GmailClient._extract_body(payload) == "Hello there\nTotal: 123"
