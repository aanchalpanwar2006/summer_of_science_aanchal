import base64

import gmail_client


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def _decode(raw: str) -> str:
    padded = raw + "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(padded).decode()


def test_build_mime_message_basic():
    result = gmail_client.build_mime_message("to@example.com", "Hello", "Body text")

    assert "raw" in result
    assert "threadId" not in result
    decoded = _decode(result["raw"])
    assert "Body text" in decoded
    assert "Hello" in decoded


def test_build_mime_message_reply_headers():
    result = gmail_client.build_mime_message(
        "to@example.com",
        "Re: Hello",
        "Reply body",
        thread_id="thread123",
        in_reply_to_message_id="<msg1@mail.gmail.com>",
        references="<msg0@mail.gmail.com>",
    )

    assert result["threadId"] == "thread123"
    decoded = _decode(result["raw"])
    assert "In-Reply-To: <msg1@mail.gmail.com>" in decoded
    assert "References: <msg0@mail.gmail.com>" in decoded


def test_extract_headers():
    message = {
        "payload": {
            "headers": [
                {"name": "From", "value": "Alice <alice@example.com>"},
                {"name": "Subject", "value": "Hi there"},
                {"name": "Date", "value": "Mon, 1 Jan 2024 00:00:00 +0000"},
                {"name": "Message-ID", "value": "<abc@mail.gmail.com>"},
            ]
        }
    }

    headers = gmail_client.extract_headers(message)

    assert headers["from"] == "Alice <alice@example.com>"
    assert headers["subject"] == "Hi there"
    assert headers["message_id"] == "<abc@mail.gmail.com>"
    assert headers["references"] == ""


def test_extract_plain_text_body_simple():
    message = {"payload": {"mimeType": "text/plain", "body": {"data": _b64("Hello world")}}}
    assert gmail_client.extract_plain_text_body(message) == "Hello world"


def test_extract_plain_text_body_multipart_prefers_plain():
    message = {
        "payload": {
            "mimeType": "multipart/alternative",
            "parts": [
                {"mimeType": "text/plain", "body": {"data": _b64("Plain version")}},
                {"mimeType": "text/html", "body": {"data": _b64("<p>HTML version</p>")}},
            ],
        }
    }
    assert gmail_client.extract_plain_text_body(message) == "Plain version"


def test_extract_plain_text_body_falls_back_to_html():
    message = {
        "payload": {
            "mimeType": "multipart/alternative",
            "parts": [
                {"mimeType": "text/html", "body": {"data": _b64("<p>Only HTML</p>")}},
            ],
        }
    }
    assert gmail_client.extract_plain_text_body(message) == "Only HTML"


def test_send_message_calls_gmail_api():
    calls = {}

    class FakeExecute:
        def execute(self):
            return {"id": "msg1", "threadId": "thread1"}

    class FakeMessages:
        def send(self, userId, body):
            calls["userId"] = userId
            calls["body"] = body
            return FakeExecute()

    class FakeUsers:
        def messages(self):
            return FakeMessages()

    class FakeService:
        def users(self):
            return FakeUsers()

    result = gmail_client.send_message(FakeService(), "to@example.com", "Subject", "Body")

    assert result == {"id": "msg1", "threadId": "thread1"}
    assert calls["userId"] == "me"
    assert "raw" in calls["body"]
