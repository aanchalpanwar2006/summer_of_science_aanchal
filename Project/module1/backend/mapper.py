import json
import os
import re
from difflib import SequenceMatcher
from typing import Optional

from models import FormField

FUZZY_THRESHOLD = 0.8

ALIASES: dict[str, str] = {
    "full name": "name",
    "your name": "name",
    "first name": "first_name",
    "last name": "last_name",
    "email address": "email",
    "e-mail": "email",
    "mobile": "phone",
    "mobile number": "phone",
    "phone number": "phone",
    "contact number": "phone",
    "current address": "address",
    "home address": "address",
    "college": "college",
    "college/university": "college",
    "cv": "resume_path",
    "resume": "resume_path",
    "linkedin": "linkedin_url",
    "linkedin url": "linkedin_url",
    "linkedin profile": "linkedin_url",
    "github": "github_url",
    "github url": "github_url",
}


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "field"


def _fuzzy_best_match(label: str, keys: list[str]) -> Optional[str]:
    best_key, best_ratio = None, 0.0
    for key in keys:
        ratio = SequenceMatcher(None, label, key.replace("_", " ")).ratio()
        if ratio > best_ratio:
            best_key, best_ratio = key, ratio
    return best_key if best_ratio >= FUZZY_THRESHOLD else None


def _resolve_deterministic(field: FormField, profile: dict[str, str]) -> Optional[str]:
    normalized_label = _normalize(field.label)
    normalized_keys = {key.replace("_", " "): key for key in profile}

    if normalized_label in normalized_keys:
        return normalized_keys[normalized_label]

    alias_key = ALIASES.get(normalized_label)
    if alias_key and alias_key in profile:
        return alias_key

    return _fuzzy_best_match(normalized_label, list(profile.keys()))


def _llm_resolve_batch(labels: list[str], profile_keys: list[str]) -> dict[str, str]:
    """One batched LLM call to map remaining unresolved labels to profile keys.
    Returns {label: resolved_or_new_key}. Falls back to slugified labels on any failure."""
    try:
        import openai

        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        system_prompt = (
            "You map form field labels to a user's profile keys. "
            "Given a list of labels and a list of existing profile keys, "
            "for each label return either an existing profile key that means the same thing, "
            "or a new short snake_case key if nothing matches. "
            'Respond ONLY with JSON: {"label": "resolved_key", ...}'
        )
        user_prompt = json.dumps({"labels": labels, "existing_profile_keys": profile_keys})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=512,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
        return json.loads(raw)
    except Exception:
        return {label: _slugify(label) for label in labels}


def map_fields(fields: list[FormField], profile: dict[str, str]) -> list[FormField]:
    unresolved: list[FormField] = []

    for field in fields:
        if field.element_type == "file":
            field.mapped_key = "resume_path"
            if profile.get("resume_path"):
                field.proposed_value = profile["resume_path"]
                field.source = "profile"
            else:
                field.source = "missing"
            continue

        resolved_key = _resolve_deterministic(field, profile)
        if resolved_key:
            field.mapped_key = resolved_key
            field.proposed_value = profile[resolved_key]
            field.source = "profile"
        else:
            unresolved.append(field)

    if unresolved and os.environ.get("OPENAI_API_KEY"):
        labels = [field.label for field in unresolved]
        mapping = _llm_resolve_batch(labels, list(profile.keys()))
        for field in unresolved:
            key = mapping.get(field.label, _slugify(field.label))
            field.mapped_key = key
            if key in profile:
                field.proposed_value = profile[key]
                field.source = "profile"
            else:
                field.source = "missing"
    else:
        for field in unresolved:
            field.mapped_key = _slugify(field.label)
            field.source = "missing"

    return fields
