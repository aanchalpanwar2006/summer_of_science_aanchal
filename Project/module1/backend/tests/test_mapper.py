from mapper import map_fields
from models import FormField


def make_field(field_id: str, label: str, element_type: str = "text") -> FormField:
    return FormField(field_id=field_id, label=label, element_type=element_type)


def test_exact_match_resolves_from_profile(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    profile = {"email": "person@example.com"}
    fields = [make_field("1", "Email")]

    result = map_fields(fields, profile)

    assert result[0].mapped_key == "email"
    assert result[0].proposed_value == "person@example.com"
    assert result[0].source == "profile"


def test_alias_match_resolves_from_profile(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    profile = {"phone": "1234567890"}
    fields = [make_field("1", "Mobile Number")]

    result = map_fields(fields, profile)

    assert result[0].mapped_key == "phone"
    assert result[0].proposed_value == "1234567890"
    assert result[0].source == "profile"


def test_fuzzy_match_resolves_close_typo(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    profile = {"college": "MIT"}
    fields = [make_field("1", "Collage")]

    result = map_fields(fields, profile)

    assert result[0].mapped_key == "college"
    assert result[0].proposed_value == "MIT"
    assert result[0].source == "profile"


def test_unresolvable_label_becomes_missing_without_llm(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    profile = {"email": "person@example.com"}
    fields = [make_field("1", "Twitter Handle")]

    result = map_fields(fields, profile)

    assert result[0].mapped_key == "twitter_handle"
    assert result[0].source == "missing"
    assert result[0].proposed_value == ""


def test_file_field_maps_to_resume_path(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with_resume = map_fields([make_field("1", "Resume", "file")], {"resume_path": "/tmp/resume.pdf"})
    assert with_resume[0].mapped_key == "resume_path"
    assert with_resume[0].source == "profile"
    assert with_resume[0].proposed_value == "/tmp/resume.pdf"

    without_resume = map_fields([make_field("2", "Resume", "file")], {})
    assert without_resume[0].mapped_key == "resume_path"
    assert without_resume[0].source == "missing"
