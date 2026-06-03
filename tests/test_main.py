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
                links=["https://portal.petrolimex.com.vn/invoice?id=123"],
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
    output = capsys.readouterr().out
    assert "Saved 1 message(s) to emails.txt as text." in output
    assert "Snippet: Your receipt is ready" in output
    assert "https://portal.petrolimex.com.vn/invoice?id=123" in output
    assert "Body:\nFull receipt body" in output


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
    output = capsys.readouterr().out
    assert "Saved 1 message(s) to emails.json as json." in output
    assert "Snippet: Your receipt is ready" in output
    assert "https://portal.petrolimex.com.vn/invoice?id=123" in output
    assert "Body:\nFull receipt body" in output


def test_main_runs_form_automation_when_requested(monkeypatch, capsys):
    calls = []
    writes = []

    class Result:
        status = "submitted"

    def fake_automate_email_forms(emails, config_path, link_index, submit):
        calls.append((emails, config_path, link_index, submit))
        return [Result()]

    def fake_write_automation_results(results, output_path):
        writes.append((results, output_path))

    monkeypatch.setattr(main, "GmailClient", FakeGmailClient)
    monkeypatch.setattr(main, "automate_email_forms", fake_automate_email_forms)
    monkeypatch.setattr(main, "write_automation_results", fake_write_automation_results)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "label:Petrolimex",
            "--max",
            "1",
            "--automate-form",
            "--form-config",
            "config/form_automation.json",
            "--link-index",
            "0",
            "--submit-form",
            "--automation-output",
            "results.json",
        ],
    )

    main.main()

    assert len(calls) == 1
    emails, config_path, link_index, submit = calls[0]
    assert len(emails) == 1
    assert config_path == "config/form_automation.json"
    assert link_index == 0
    assert submit is True
    assert len(writes) == 1
    assert writes[0][0][0].status == "submitted"
    assert writes[0][1] == "results.json"
    output = capsys.readouterr().out
    assert "Automated 1 URL form(s): 1 submitted, 0 filled without submit, 0 failed." in output
