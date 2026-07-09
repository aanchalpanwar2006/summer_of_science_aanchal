import base64
import re
from email.mime.text import MIMEText
from typing import Optional


def build_mime_message(
    to: str,
    subject: str,
    body: str,
    thread_id: Optional[str] = None,
    in_reply_to_message_id: Optional[str] = None,
    references: Optional[str] = None,
) -> dict:
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    if in_reply_to_message_id:
        message["In-Reply-To"] = in_reply_to_message_id
    if references:
        message["References"] = references

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    result = {"raw": raw}
    if thread_id:
        result["threadId"] = thread_id
    return result


def send_message(
    service,
    to: str,
    subject: str,
    body: str,
    thread_id: Optional[str] = None,
    in_reply_to_message_id: Optional[str] = None,
    references: Optional[str] = None,
) -> dict:
    mime_body = build_mime_message(to, subject, body, thread_id, in_reply_to_message_id, references)
    return service.users().messages().send(userId="me", body=mime_body).execute()


def list_unread(service, max_results: int = 20) -> list[dict]:
    response = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["UNREAD"], maxResults=max_results)
        .execute()
    )
    return response.get("messages", [])


def get_message(service, message_id: str, format: str = "metadata") -> dict:
    return (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format=format, metadataHeaders=["From", "Subject", "Date"])
        .execute()
    )


def get_message_full(service, message_id: str) -> dict:
    return service.users().messages().get(userId="me", id=message_id, format="full").execute()


def get_thread(service, thread_id: str) -> dict:
    return service.users().threads().get(userId="me", id=thread_id, format="full").execute()


def _decode_part_data(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def extract_plain_text_body(gmail_message: dict) -> str:
    payload = gmail_message.get("payload", {})

    def walk(part: dict) -> dict:
        mime_type = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        found = {}
        if data and mime_type in ("text/plain", "text/html"):
            found[mime_type] = _decode_part_data(data)
        for sub_part in part.get("parts", []) or []:
            for mime_type, text in walk(sub_part).items():
                found.setdefault(mime_type, text)
        return found

    parts_found = walk(payload)
    if "text/plain" in parts_found:
        return parts_found["text/plain"]
    if "text/html" in parts_found:
        return _strip_html(parts_found["text/html"])
    return ""


def extract_headers(gmail_message: dict) -> dict:
    headers = gmail_message.get("payload", {}).get("headers", [])
    lookup = {h["name"].lower(): h["value"] for h in headers}
    return {
        "from": lookup.get("from", ""),
        "subject": lookup.get("subject", ""),
        "date": lookup.get("date", ""),
        "message_id": lookup.get("message-id", ""),
        "references": lookup.get("references", ""),
    }
