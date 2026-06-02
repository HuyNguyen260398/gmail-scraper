import base64
import quopri
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gmail_client import GmailClient


def encoded(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii").rstrip("=")


def encoded_quoted_printable(text: str) -> str:
    quoted_printable = quopri.encodestring(text.encode("utf-8"))
    return base64.urlsafe_b64encode(quoted_printable).decode("ascii").rstrip("=")


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


def test_extract_links_reads_hidden_html_anchor_href():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {
                    "data": encoded(
                        "Quý khách vui lòng truy cập địa chỉ website portal link."
                    )
                },
            },
            {
                "mimeType": "text/html",
                "body": {
                    "data": encoded(
                        "<p>Quý khách vui lòng truy cập địa chỉ website portal "
                        '<a href="https://portal.petrolimex.com.vn/invoice?id=123">'
                        "link</a> để tra cứu $invName của mình.</p>"
                    )
                },
            },
        ],
    }

    assert GmailClient._extract_links(payload) == [
        "https://portal.petrolimex.com.vn/invoice?id=123"
    ]


def test_extract_links_reads_quoted_printable_html_anchor_href():
    payload = {
        "mimeType": "text/html",
        "headers": [
            {"name": "Content-Transfer-Encoding", "value": "quoted-printable"}
        ],
        "body": {
            "data": encoded_quoted_printable(
                "<p>Quý khách vui lòng truy cập địa chỉ website portal "
                '<a href="https://portal.petrolimex.com.vn/invoice?id=123">'
                "link</a> để tra cứu $invName của mình.</p>"
            )
        },
    }

    assert GmailClient._extract_links(payload) == [
        "https://portal.petrolimex.com.vn/invoice?id=123"
    ]


def test_extract_links_handles_quoted_printable_html_without_header():
    payload = {
        "mimeType": "text/html",
        "body": {
            "data": encoded_quoted_printable(
                "<p>Quý khách vui lòng truy cập địa chỉ website portal "
                '<a href="https://portal.petrolimex.com.vn/invoice?id=123">'
                "link</a> để tra cứu $invName của mình.</p>"
            )
        },
    }

    assert GmailClient._extract_links(payload) == [
        "https://portal.petrolimex.com.vn/invoice?id=123"
    ]


def test_extract_links_reads_plain_text_urls_and_deduplicates():
    payload = {
        "mimeType": "multipart/mixed",
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {
                    "data": encoded(
                        "View https://example.com/invoice/123. "
                        "Again https://example.com/invoice/123"
                    )
                },
            },
            {
                "mimeType": "text/html",
                "body": {
                    "data": encoded(
                        '<a href="https://example.com/invoice/123">invoice</a>'
                    )
                },
            },
        ],
    }

    assert GmailClient._extract_links(payload) == [
        "https://example.com/invoice/123"
    ]
