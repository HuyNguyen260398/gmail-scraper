import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import form_automation
from form_automation import load_form_automation_config, resolve_field_values
from gmail_client import Email


ROOT = Path(__file__).resolve().parents[1]


def sample_body() -> str:
    return (ROOT / "assets" / "sample-email-content.txt").read_text(encoding="utf-8")


def sample_email(body: str) -> Email:
    return Email(
        id="msg-1",
        thread_id="thread-1",
        subject="Petrolimex invoice",
        sender="Petrolimex <billing@example.com>",
        date="Wed, 03 Jun 2026 08:00:00 +0700",
        snippet="Mã tra cứu: FN2V8BMAG*",
        body=body,
        labels=["INBOX"],
        links=["https://hoadon.petrolimex.com.vn/SearchInvoicebycode/Index"],
    )


def write_config(tmp_path, field_values):
    path = tmp_path / "form_automation.json"
    path.write_text(
        json.dumps(
            {
                "url_allowlist": ["hoadon.petrolimex.com.vn"],
                "field_values": field_values,
                "form_fields": [],
            }
        ),
        encoding="utf-8",
    )
    return load_form_automation_config(str(path))


def test_extract_invoice_lookup_code_from_sample_email_content():
    assert form_automation.extract_invoice_lookup_code(sample_body()) == "FN2V8BMAG*"


def test_resolve_field_values_supports_petrolimex_invoice_code_source(tmp_path):
    config = write_config(
        tmp_path,
        [{"key": "invoice_code", "source": "petrolimex_invoice_code"}],
    )

    assert resolve_field_values(sample_email(sample_body()), config) == {
        "invoice_code": "FN2V8BMAG*"
    }


def test_resolve_field_values_rejects_missing_petrolimex_invoice_code(tmp_path):
    config = write_config(
        tmp_path,
        [{"key": "invoice_code", "source": "petrolimex_invoice_code"}],
    )

    with pytest.raises(ValueError, match="Petrolimex invoice lookup code not found"):
        resolve_field_values(sample_email("No invoice lookup code here."), config)
