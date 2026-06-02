"""Thin wrapper around the Gmail API for listing and reading messages."""

import base64
from dataclasses import dataclass, field

from googleapiclient.discovery import build

from auth import get_credentials


@dataclass
class Email:
    id: str
    thread_id: str
    subject: str
    sender: str
    date: str
    snippet: str
    body: str = ""
    labels: list = field(default_factory=list)


class GmailClient:
    def __init__(self):
        self.service = build("gmail", "v1", credentials=get_credentials())

    def list_message_ids(self, query: str = "", max_results: int = 50) -> list[str]:
        """List message IDs matching a Gmail search query.

        `query` uses Gmail search syntax, e.g.:
            "label:Petrolimex"
            "label:Petrolimex is:unread newer_than:7d"
            "from:billing@example.com"
        """
        ids: list[str] = []
        page_token = None

        while True:
            resp = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    q=query,
                    maxResults=min(max_results - len(ids), 100),
                    pageToken=page_token,
                )
                .execute()
            )
            ids.extend(m["id"] for m in resp.get("messages", []))
            page_token = resp.get("nextPageToken")
            if not page_token or len(ids) >= max_results:
                break

        return ids[:max_results]

    def get_email(self, message_id: str) -> Email:
        """Fetch and parse a single message into an Email object."""
        msg = (
            self.service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        headers = {
            h["name"].lower(): h["value"]
            for h in msg["payload"].get("headers", [])
        }

        return Email(
            id=msg["id"],
            thread_id=msg["threadId"],
            subject=headers.get("subject", "(no subject)"),
            sender=headers.get("from", ""),
            date=headers.get("date", ""),
            snippet=msg.get("snippet", ""),
            body=self._extract_body(msg["payload"]),
            labels=msg.get("labelIds", []),
        )

    def fetch(self, query: str = "", max_results: int = 50) -> list[Email]:
        """Convenience: list + get in one call."""
        return [self.get_email(mid) for mid in self.list_message_ids(query, max_results)]

    @staticmethod
    def _extract_body(payload: dict) -> str:
        """Walk the MIME tree and return the plain-text body if present."""

        def decode(data: str) -> str:
            return base64.urlsafe_b64decode(data.encode()).decode(
                "utf-8", errors="replace"
            )

        # Single-part message
        if payload.get("mimeType", "").startswith("text/plain"):
            data = payload.get("body", {}).get("data")
            if data:
                return decode(data)

        # Multipart: prefer text/plain, fall back to first text/html
        html_fallback = ""
        for part in payload.get("parts", []):
            mime = part.get("mimeType", "")
            data = part.get("body", {}).get("data")
            if mime == "text/plain" and data:
                return decode(data)
            if mime == "text/html" and data and not html_fallback:
                html_fallback = decode(data)
            # Nested multipart
            if part.get("parts"):
                nested = GmailClient._extract_body(part)
                if nested:
                    return nested

        return html_fallback
