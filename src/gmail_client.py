"""Thin wrapper around the Gmail API for listing and reading messages."""

import base64
import quopri
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import unquote

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
    links: list = field(default_factory=list)


class _HTMLTextExtractor(HTMLParser):
    """Convert an HTML email part into readable plain text."""

    BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "div",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "p",
        "pre",
        "section",
        "table",
        "tr",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style"}:
            self._ignored_depth += 1
            return
        if self._ignored_depth == 0 and tag in self.BLOCK_TAGS:
            self._append_newline()

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth > 0:
            self._ignored_depth -= 1
            return
        if self._ignored_depth == 0 and tag in self.BLOCK_TAGS:
            self._append_newline()

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0:
            self._chunks.append(data)

    def get_text(self) -> str:
        lines = []
        for line in "".join(self._chunks).splitlines():
            normalized = " ".join(line.split())
            if normalized:
                lines.append(normalized)
        return "\n".join(lines)

    def _append_newline(self) -> None:
        if self._chunks and not self._chunks[-1].endswith("\n"):
            self._chunks.append("\n")


class _HTMLLinkExtractor(HTMLParser):
    """Extract HTTP links from HTML anchor tags."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style"}:
            self._ignored_depth += 1
            return
        if self._ignored_depth > 0 or tag != "a":
            return

        attributes = dict(attrs)
        href = attributes.get("href", "")
        if href.startswith(("http://", "https://")):
            self.links.append(unquote(href))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth > 0:
            self._ignored_depth -= 1


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
            links=self._extract_links(msg["payload"]),
        )

    def fetch(self, query: str = "", max_results: int = 50) -> list[Email]:
        """Convenience: list + get in one call."""
        return [self.get_email(mid) for mid in self.list_message_ids(query, max_results)]

    @staticmethod
    def _extract_body(payload: dict) -> str:
        """Walk the MIME tree and return all inline body text in MIME order."""

        plain_parts = GmailClient._collect_text_parts(payload, "text/plain")
        if plain_parts:
            return "\n\n".join(part.strip() for part in plain_parts if part.strip())

        html_parts = GmailClient._collect_text_parts(payload, "text/html")
        if not html_parts:
            return ""

        text_parts = []
        for html_part in html_parts:
            parser = _HTMLTextExtractor()
            parser.feed(html_part)
            text = parser.get_text()
            if text:
                text_parts.append(text)

        return "\n\n".join(text_parts)

    @staticmethod
    def _extract_links(payload: dict) -> list[str]:
        """Extract HTTP links from inline plain-text and HTML MIME parts."""
        links: list[str] = []

        for plain_part in GmailClient._collect_text_parts(payload, "text/plain"):
            links.extend(GmailClient._extract_plain_text_links(plain_part))

        for html_part in GmailClient._collect_text_parts(payload, "text/html"):
            parser = _HTMLLinkExtractor()
            parser.feed(html_part)
            links.extend(parser.links)

        return GmailClient._dedupe_preserving_order(links)

    @staticmethod
    def _extract_plain_text_links(text: str) -> list[str]:
        links = re.findall(r"https?://[^\s<>()\"']+", text)
        return [link.rstrip(".,;:!?]") for link in links]

    @staticmethod
    def _collect_text_parts(payload: dict, mime_type: str) -> list[str]:
        if GmailClient._has_attachment_disposition(payload):
            return []

        collected: list[str] = []
        current_mime = payload.get("mimeType", "")
        data = payload.get("body", {}).get("data")
        if current_mime == mime_type and data:
            collected.append(GmailClient._decode_body_data(data, payload))

        for child in payload.get("parts", []):
            collected.extend(GmailClient._collect_text_parts(child, mime_type))

        return collected

    @staticmethod
    def _decode_body_data(data: str, part=None) -> str:
        padded_data = data + "=" * (-len(data) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded_data.encode())

        transfer_encoding = GmailClient._header_value(
            part or {}, "content-transfer-encoding"
        ).lower()
        if transfer_encoding == "quoted-printable":
            decoded_bytes = quopri.decodestring(decoded_bytes)
        elif GmailClient._looks_quoted_printable(decoded_bytes):
            decoded_bytes = quopri.decodestring(decoded_bytes)
        elif transfer_encoding == "base64":
            try:
                decoded_bytes = base64.b64decode(decoded_bytes, validate=True)
            except ValueError:
                pass

        return decoded_bytes.decode("utf-8", errors="replace")

    @staticmethod
    def _header_value(part: dict, name: str) -> str:
        for header in part.get("headers", []):
            if header.get("name", "").lower() == name:
                return header.get("value", "")
        return ""

    @staticmethod
    def _looks_quoted_printable(decoded_bytes: bytes) -> bool:
        lowered = decoded_bytes.lower()
        return b"href=3d" in lowered or b"https=3a" in lowered or b"=\r\n" in lowered

    @staticmethod
    def _has_attachment_disposition(part: dict) -> bool:
        headers = part.get("headers", [])
        for header in headers:
            if header.get("name", "").lower() == "content-disposition":
                return header.get("value", "").lower().startswith("attachment")
        return bool(part.get("filename"))

    @staticmethod
    def _dedupe_preserving_order(items: list[str]) -> list[str]:
        deduped = []
        seen = set()
        for item in items:
            if item not in seen:
                deduped.append(item)
                seen.add(item)
        return deduped
