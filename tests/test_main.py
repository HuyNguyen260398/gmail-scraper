import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import main
from gmail_client import Email


class FakeGmailClient:
    def fetch(self, query: str, max_results: int) -> list[Email]:
        assert query == "label:Petrolimex"
        assert max_results == 1
        return [
            Email(
                id="msg-1",
                thread_id="thread-1",
                subject="Fuel receipt",
                sender="billing@example.com",
                date="Tue, 02 Jun 2026 08:00:00 +0700",
                snippet="Your receipt is ready",
                body="Full receipt body",
                labels=["INBOX"],
            )
        ]


def test_main_writes_requested_output_file(monkeypatch, capsys):
    calls = []

    def fake_write_emails(emails, output_path, output_format):
        calls.append((emails, output_path, output_format))

    monkeypatch.setattr(main, "GmailClient", FakeGmailClient)
    monkeypatch.setattr(main, "write_emails", fake_write_emails)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "label:Petrolimex",
            "--max",
            "1",
            "--output",
            "emails.txt",
            "--format",
            "text",
        ],
    )

    main.main()

    assert len(calls) == 1
    emails, output_path, output_format = calls[0]
    assert len(emails) == 1
    assert output_path == "emails.txt"
    assert output_format == "text"
    assert "Saved 1 message(s) to emails.txt as text." in capsys.readouterr().out


def test_main_uses_json_output_format_by_default(monkeypatch, capsys):
    calls = []

    def fake_write_emails(emails, output_path, output_format):
        calls.append((emails, output_path, output_format))

    monkeypatch.setattr(main, "GmailClient", FakeGmailClient)
    monkeypatch.setattr(main, "write_emails", fake_write_emails)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "label:Petrolimex",
            "--max",
            "1",
            "--output",
            "emails.json",
        ],
    )

    main.main()

    assert len(calls) == 1
    emails, output_path, output_format = calls[0]
    assert len(emails) == 1
    assert output_path == "emails.json"
    assert output_format == "json"
    assert "Saved 1 message(s) to emails.json as json." in capsys.readouterr().out
