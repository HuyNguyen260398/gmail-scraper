import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from exporter import (
    email_to_dict,
    invoice_lookup_to_dict,
    write_emails,
    write_invoice_lookup_codes,
    write_json,
    write_text,
)
from gmail_client import Email


def sample_email() -> Email:
    return Email(
        id="msg-1",
        thread_id="thread-1",
        subject="Fuel receipt",
        sender="billing@example.com",
        date="Tue, 02 Jun 2026 08:00:00 +0700",
        snippet="Your receipt is ready",
        body="Full receipt body",
        labels=["INBOX", "Petrolimex"],
        links=["https://portal.petrolimex.com.vn/invoice?id=123"],
    )


def sample_petrolimex_email() -> Email:
    email = sample_email()
    email.body = "Thông tin hóa đơn\nMã tra cứu: FN2V8BMAG*"
    email.links = ["https://hoadon.petrolimex.com.vn/SearchInvoicebycode/Index"]
    return email


def test_email_to_dict_includes_all_email_fields():
    assert email_to_dict(sample_email()) == {
        "id": "msg-1",
        "thread_id": "thread-1",
        "subject": "Fuel receipt",
        "sender": "billing@example.com",
        "date": "Tue, 02 Jun 2026 08:00:00 +0700",
        "snippet": "Your receipt is ready",
        "body": "Full receipt body",
        "labels": ["INBOX", "Petrolimex"],
        "links": ["https://portal.petrolimex.com.vn/invoice?id=123"],
    }


def test_write_json_writes_utf8_indented_array(tmp_path):
    output_path = tmp_path / "emails.json"

    write_json([sample_email()], str(output_path))

    assert json.loads(output_path.read_text(encoding="utf-8")) == [
        email_to_dict(sample_email())
    ]
    assert output_path.read_text(encoding="utf-8").startswith("[\n  {")


def test_invoice_lookup_to_dict_includes_code_url_and_field_values():
    assert invoice_lookup_to_dict(sample_petrolimex_email()) == {
        "email_id": "msg-1",
        "thread_id": "thread-1",
        "subject": "Fuel receipt",
        "date": "Tue, 02 Jun 2026 08:00:00 +0700",
        "url": "https://hoadon.petrolimex.com.vn/SearchInvoicebycode/Index",
        "invoice_code": "FN2V8BMAG*",
        "field_values": {"invoice_code": "FN2V8BMAG*"},
    }


def test_write_invoice_lookup_codes_writes_automation_handoff_json(tmp_path):
    output_path = tmp_path / "invoice-codes.json"

    write_invoice_lookup_codes([sample_petrolimex_email()], str(output_path))

    assert json.loads(output_path.read_text(encoding="utf-8")) == [
        invoice_lookup_to_dict(sample_petrolimex_email())
    ]


def test_write_text_writes_readable_email_sections(tmp_path):
    output_path = tmp_path / "emails.txt"

    write_text([sample_email()], str(output_path))

    content = output_path.read_text(encoding="utf-8")
    assert "Email 1" in content
    assert "Date: Tue, 02 Jun 2026 08:00:00 +0700" in content
    assert "From: billing@example.com" in content
    assert "Subject: Fuel receipt" in content
    assert "Labels: INBOX, Petrolimex" in content
    assert "Snippet: Your receipt is ready" in content
    assert "Links:\nhttps://portal.petrolimex.com.vn/invoice?id=123" in content
    assert "Body:\nFull receipt body" in content
    assert "=" * 80 in content


def test_write_emails_writes_json_format(tmp_path):
    output_path = tmp_path / "emails.json"

    write_emails([sample_email()], str(output_path), "json")

    assert json.loads(output_path.read_text(encoding="utf-8")) == [
        email_to_dict(sample_email())
    ]


def test_write_emails_writes_text_format(tmp_path):
    output_path = tmp_path / "emails.txt"

    write_emails([sample_email()], str(output_path), "text")

    content = output_path.read_text(encoding="utf-8")
    assert "Email 1" in content
    assert "Links:\nhttps://portal.petrolimex.com.vn/invoice?id=123" in content
    assert "Body:\nFull receipt body" in content


def test_write_emails_rejects_unsupported_format(tmp_path):
    with pytest.raises(ValueError, match="Unsupported output format"):
        write_emails([sample_email()], str(tmp_path / "emails.csv"), "csv")
