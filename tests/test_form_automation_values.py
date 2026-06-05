import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from form_automation import (
    build_email_context,
    load_form_automation_config,
    load_form_automation_input,
    resolve_field_values,
)
from gmail_client import Email


def sample_email() -> Email:
    return Email(
        id="msg-1",
        thread_id="thread-1",
        subject="Invoice INV-123",
        sender="Billing Team <billing@example.com>",
        date="Tue, 02 Jun 2026 08:00:00 +0700",
        snippet="Total: 450000 VND",
        body="Customer code: CUST-9\nInvoice amount: 450000",
        labels=["INBOX"],
        links=[
            "https://portal.example.com/form?id=123",
            "https://portal.example.com/backup",
        ],
    )


def load_config(tmp_path, field_values):
    path = tmp_path / "form_automation.json"
    path.write_text(
        json.dumps(
            {
                "url_allowlist": ["portal.example.com"],
                "field_values": field_values,
                "form_fields": [],
            }
        ),
        encoding="utf-8",
    )
    return load_form_automation_config(str(path))


def test_build_email_context_includes_sender_email_and_links():
    context = build_email_context(sample_email())

    assert context["sender_email"] == "billing@example.com"
    assert context["first_link"] == "https://portal.example.com/form?id=123"
    assert "https://portal.example.com/backup" in context["links_joined"]
    assert context["body"].startswith("Customer code")


def test_resolve_field_values_from_subject_snippet_and_body(tmp_path):
    config = load_config(
        tmp_path,
        [
            {"key": "invoice_id", "source": "subject", "regex": "(INV-\\d+)"},
            {"key": "total", "source": "snippet", "regex": "Total: (\\d+)"},
            {"key": "customer_code", "source": "body", "regex": "Customer code: ([A-Z0-9-]+)"},
        ],
    )

    assert resolve_field_values(sample_email(), config) == {
        "invoice_id": "INV-123",
        "total": "450000",
        "customer_code": "CUST-9",
    }


def test_resolve_field_values_uses_default_when_regex_misses(tmp_path):
    config = load_config(
        tmp_path,
        [
            {
                "key": "optional_code",
                "source": "body",
                "regex": "Missing: (\\w+)",
                "default": "N/A",
            }
        ],
    )

    assert resolve_field_values(sample_email(), config) == {"optional_code": "N/A"}


def test_load_form_automation_input_reads_exported_invoice_code_records(tmp_path):
    path = tmp_path / "invoice-codes.json"
    path.write_text(
        json.dumps(
            [
                {
                    "email_id": "msg-1",
                    "url": "https://hoadon.petrolimex.com.vn/SearchInvoicebycode/Index",
                    "invoice_code": "FN2V8BMAG*",
                }
            ]
        ),
        encoding="utf-8",
    )

    records = load_form_automation_input(str(path))

    assert len(records) == 1
    assert records[0].email_id == "msg-1"
    assert records[0].url == "https://hoadon.petrolimex.com.vn/SearchInvoicebycode/Index"
    assert records[0].field_values == {"invoice_code": "FN2V8BMAG*"}
