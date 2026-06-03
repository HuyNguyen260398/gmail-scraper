"""Petrolimex email parsing helpers."""

import re


def extract_invoice_lookup_code(text: str) -> str | None:
    """Extract a Petrolimex invoice lookup code from email body text."""
    match = re.search(r"Mã\s+tra\s+cứu\s*:\s*([^\s\r\n]+)", text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()
