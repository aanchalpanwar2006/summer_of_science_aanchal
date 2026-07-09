import json
import os
from typing import Optional


def _parse_json_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
    return json.loads(raw)


def _chat(system_prompt: str, user_prompt: str, max_tokens: int = 400) -> str:
    import openai

    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


def draft_compose(intent: str, sender_name: Optional[str] = None) -> dict:
    system_prompt = (
        "You draft professional emails from a one-sentence intent. "
        "Respond ONLY with JSON: {\"subject\": \"...\", \"body\": \"...\"}. "
        "Infer an appropriate tone from the intent. Do not invent a recipient "
        "email address or name if one isn't given — address the recipient generically "
        "(e.g. 'Hi,') unless the intent names them. "
        + (f"Sign the email as {sender_name} if a sign-off is appropriate." if sender_name else "")
    )
    raw = _chat(system_prompt, intent)
    return _parse_json_response(raw)


def draft_reply(intent: str, thread_context: list) -> dict:
    system_prompt = (
        "You draft a reply email given the prior messages in a thread and the user's "
        "intent for what the reply should say. Respond ONLY with JSON: "
        "{\"subject\": \"...\", \"body\": \"...\"}. The subject should usually be "
        "'Re: <original subject>' unless the intent implies otherwise. The body should "
        "address the intent directly without re-quoting the full prior thread inline "
        "(the email client already threads/quotes automatically)."
    )
    user_prompt = json.dumps({"thread": thread_context, "intent": intent})
    raw = _chat(system_prompt, user_prompt)
    return _parse_json_response(raw)


def summarize_email(sender: str, subject: str, body: str) -> str:
    system_prompt = (
        "Summarize this email in one short plain-English sentence. "
        "Respond with just the sentence, no quotes, no markdown."
    )
    user_prompt = json.dumps({"from": sender, "subject": subject, "body": body[:2000]})
    return _chat(system_prompt, user_prompt, max_tokens=80).strip()
