import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from form_automation import is_allowed_url, select_email_url
from gmail_client import Email


def email_with_links(links) -> Email:
    return Email(
        id="msg-1",
        thread_id="thread-1",
        subject="Fuel receipt",
        sender="billing@example.com",
        date="Tue, 02 Jun 2026 08:00:00 +0700",
        snippet="Receipt ready",
        body="Body",
        labels=["INBOX"],
        links=links,
    )


def test_select_email_url_uses_zero_based_https_link_index():
    email = email_with_links(
        [
            "http://portal.example.com/insecure",
            "https://portal.example.com/first",
            "https://portal.example.com/second",
        ]
    )

    assert select_email_url(email, 0) == "https://portal.example.com/first"
    assert select_email_url(email, 1) == "https://portal.example.com/second"


def test_select_email_url_returns_none_for_missing_or_negative_index():
    email = email_with_links(["https://portal.example.com/first"])

    assert select_email_url(email, -1) is None
    assert select_email_url(email, 2) is None


def test_is_allowed_url_accepts_exact_host_and_subdomain():
    allowlist = ["example.com"]

    assert is_allowed_url("https://example.com/form", allowlist)
    assert is_allowed_url("https://portal.example.com/form", allowlist)


def test_is_allowed_url_rejects_http_and_external_hostnames():
    allowlist = ["example.com"]

    assert not is_allowed_url("http://example.com/form", allowlist)
    assert not is_allowed_url("https://badexample.com/form", allowlist)
    assert not is_allowed_url("https://example.net/form", allowlist)
