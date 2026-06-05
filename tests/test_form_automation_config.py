import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from form_automation import load_form_automation_config, resolve_field_values
from gmail_client import Email


def write_config(tmp_path, data):
    path = tmp_path / "form_automation.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def valid_config():
    return {
        "url_allowlist": ["portal.example.com"],
        "headless": True,
        "timeout_ms": 10000,
        "field_values": [
            {"key": "invoice_code", "source": "body", "regex": "Code: (\\w+)"}
        ],
        "form_fields": [
            {
                "field_key": "invoice_code",
                "selector_strategy": "label",
                "selector_value": "Invoice code",
                "input_type": "text",
            }
        ],
        "submit_selector": {
            "selector_strategy": "role",
            "selector_name": "button",
            "selector_value": "Submit",
        },
    }


def sample_email(body="Code: ABC123") -> Email:
    return Email(
        id="msg-1",
        thread_id="thread-1",
        subject="Fuel receipt",
        sender="Billing <billing@example.com>",
        date="Tue, 02 Jun 2026 08:00:00 +0700",
        snippet="Receipt ready",
        body=body,
        labels=["INBOX"],
        links=["https://portal.example.com/form"],
    )


def test_load_form_automation_config_reads_valid_config(tmp_path):
    path = write_config(tmp_path, valid_config())

    config = load_form_automation_config(str(path))

    assert config.url_allowlist == ["portal.example.com"]
    assert config.headless is True
    assert config.timeout_ms == 10000
    assert config.manual_after_fill is False
    assert config.field_values[0].key == "invoice_code"
    assert config.form_fields[0].selector_strategy == "label"
    assert config.form_fields[0].requires_manual_input is False
    assert config.submit_selector["selector_value"] == "Submit"


def test_load_form_automation_config_reads_manual_captcha_options(tmp_path):
    data = valid_config()
    data["manual_after_fill"] = True
    data["form_fields"].append(
        {
            "field_key": "captcha",
            "selector_strategy": "id",
            "selector_value": "captch",
            "input_type": "text",
            "required": True,
            "requires_manual_input": True,
        }
    )
    path = write_config(tmp_path, data)

    config = load_form_automation_config(str(path))

    assert config.manual_after_fill is True
    assert config.form_fields[1].field_key == "captcha"
    assert config.form_fields[1].requires_manual_input is True


def test_load_form_automation_config_requires_url_allowlist(tmp_path):
    data = valid_config()
    data.pop("url_allowlist")
    path = write_config(tmp_path, data)

    with pytest.raises(ValueError, match="url_allowlist"):
        load_form_automation_config(str(path))


def test_load_form_automation_config_rejects_empty_url_allowlist(tmp_path):
    data = valid_config()
    data["url_allowlist"] = []
    path = write_config(tmp_path, data)

    with pytest.raises(ValueError, match="url_allowlist"):
        load_form_automation_config(str(path))


def test_resolve_field_values_rejects_unknown_source(tmp_path):
    data = valid_config()
    data["field_values"] = [{"key": "x", "source": "unknown"}]
    config = load_form_automation_config(str(write_config(tmp_path, data)))

    with pytest.raises(ValueError, match="Unknown field value source"):
        resolve_field_values(sample_email(), config)


def test_resolve_field_values_rejects_regex_without_match(tmp_path):
    config = load_form_automation_config(str(write_config(tmp_path, valid_config())))

    with pytest.raises(ValueError, match="Regex did not match"):
        resolve_field_values(sample_email(body="No code here"), config)
