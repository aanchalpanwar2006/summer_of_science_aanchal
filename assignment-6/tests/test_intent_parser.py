import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "assignment-3"))

from intent_parser import parse_intent  # noqa: E402


def _mock_client(action_dict: dict) -> MagicMock:
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content=json.dumps(action_dict)))
    ]
    return mock_client


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
@patch("openai.OpenAI")
def test_navigate(mock_cls):
    expected = {
        "action": "navigate",
        "target_url": "https://github.com",
        "data": {},
        "steps": ["Open browser tab", "Navigate to https://github.com", "Wait for page to load"],
    }
    mock_cls.return_value = _mock_client(expected)

    result = parse_intent("go to GitHub")

    assert result["action"] == "navigate"
    assert result["target_url"].startswith("http")
    assert len(result["steps"]) > 0


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
@patch("openai.OpenAI")
def test_fill_form(mock_cls):
    expected = {
        "action": "fill_form",
        "target_url": "https://careers.example.com",
        "data": {"name": "<user name>", "email": "<user email>"},
        "steps": ["Navigate to careers page", "Fill in name", "Fill in email", "Submit"],
    }
    mock_cls.return_value = _mock_client(expected)

    result = parse_intent("apply to the job at careers.example.com")

    assert result["action"] == "fill_form"
    assert "careers" in result["target_url"]
    assert len(result["steps"]) > 0


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
@patch("openai.OpenAI")
def test_email(mock_cls):
    expected = {
        "action": "email",
        "target_url": None,
        "data": {"to": "boss@company.com", "subject": "Summary", "body": "<summary>"},
        "steps": ["Extract summary", "Open email client", "Set recipient", "Send email"],
    }
    mock_cls.return_value = _mock_client(expected)

    result = parse_intent("email this summary to my boss at boss@company.com")

    assert result["action"] == "email"
    assert result["data"]["to"] == "boss@company.com"
    assert len(result["steps"]) > 0


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
@patch("openai.OpenAI")
def test_summarize(mock_cls):
    expected = {
        "action": "summarize",
        "target_url": None,
        "data": {"output_format": "bullet points"},
        "steps": ["Extract main text", "Identify key points", "Generate summary", "Display to user"],
    }
    mock_cls.return_value = _mock_client(expected)

    result = parse_intent("summarize this article")

    assert result["action"] == "summarize"
    assert len(result["steps"]) > 0


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
@patch("openai.OpenAI")
def test_click(mock_cls):
    expected = {
        "action": "click",
        "target_url": None,
        "data": {"selector": "button:has-text('Login')"},
        "steps": ["Locate login button", "Scroll into view", "Click element", "Wait for response"],
    }
    mock_cls.return_value = _mock_client(expected)

    result = parse_intent("click the login button")

    assert result["action"] == "click"
    assert "selector" in result["data"]
    assert len(result["steps"]) > 0
