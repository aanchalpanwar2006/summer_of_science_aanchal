import json
import types

import composer


def make_fake_openai_class(content):
    class FakeOpenAI:
        def __init__(self, api_key=None):
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(
                    create=lambda **kwargs: types.SimpleNamespace(
                        choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=content))]
                    )
                )
            )

    return FakeOpenAI


def test_draft_compose_parses_json(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    content = json.dumps({"subject": "Deadline extension request", "body": "Dear Professor, ..."})
    import openai

    monkeypatch.setattr(openai, "OpenAI", make_fake_openai_class(content))

    result = composer.draft_compose("ask my professor for an extension")

    assert result["subject"] == "Deadline extension request"
    assert "Professor" in result["body"]


def test_draft_compose_strips_markdown_fence(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    payload = json.dumps({"subject": "Hi", "body": "Body text"})
    content = f"```json\n{payload}\n```"
    import openai

    monkeypatch.setattr(openai, "OpenAI", make_fake_openai_class(content))

    result = composer.draft_compose("say hi")

    assert result == {"subject": "Hi", "body": "Body text"}


def test_draft_reply_parses_json(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    content = json.dumps({"subject": "Re: Meeting", "body": "Sounds good, see you then."})
    import openai

    monkeypatch.setattr(openai, "OpenAI", make_fake_openai_class(content))

    result = composer.draft_reply(
        "confirm the meeting time",
        [{"from": "a@b.com", "date": "today", "body": "Let's meet at 3pm"}],
    )

    assert result["subject"] == "Re: Meeting"
    assert "see you then" in result["body"]


def test_summarize_email_returns_plain_string(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    content = "  The sender is asking about a refund.  "
    import openai

    monkeypatch.setattr(openai, "OpenAI", make_fake_openai_class(content))

    result = composer.summarize_email("a@b.com", "Refund", "I want a refund")

    assert result == "The sender is asking about a refund."
