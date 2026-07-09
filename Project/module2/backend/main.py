from contextlib import asynccontextmanager
from email.utils import parseaddr

from dotenv import load_dotenv

load_dotenv()

from fastapi import BackgroundTasks, FastAPI, HTTPException  # noqa: E402

import gmail_auth  # noqa: E402
import gmail_client  # noqa: E402
import composer  # noqa: E402
from drafts import create_draft, get_draft  # noqa: E402
from models import (  # noqa: E402
    ComposeRequest,
    DraftPatchRequest,
    EmailDraftState,
    InboxItem,
    InboxUnreadResponse,
    ReplyRequest,
    StartDraftResponse,
    ThreadMessage,
    ThreadResponse,
)

gmail_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global gmail_service
    creds = await gmail_auth.get_credentials()
    gmail_service = gmail_auth.build_gmail_service(creds)
    yield


app = FastAPI(
    title="Module 2 — Email Assistant",
    description="Draft, review, and send Gmail messages from a one-sentence intent.",
    version="1.0.0",
    lifespan=lifespan,
)


async def run_compose_draft(draft_id: str, intent: str) -> None:
    record = get_draft(draft_id)
    try:
        result = composer.draft_compose(intent)
        record.state.subject = result["subject"]
        record.state.body = result["body"]
        record.state.status = "awaiting_review"
    except Exception as exc:  # noqa: BLE001
        record.state.status = "error"
        record.state.error = str(exc)


async def run_reply_draft(draft_id: str, thread_id: str, intent: str) -> None:
    record = get_draft(draft_id)
    try:
        thread = gmail_client.get_thread(gmail_service, thread_id)
        messages = thread.get("messages", [])
        if not messages:
            raise ValueError(f"Thread '{thread_id}' has no messages.")

        context = []
        last_message_id = ""
        last_references = ""
        original_subject = ""
        last_sender = ""
        for msg in messages:
            headers = gmail_client.extract_headers(msg)
            body = gmail_client.extract_plain_text_body(msg)
            context.append({"from": headers["from"], "date": headers["date"], "body": body})
            last_message_id = headers["message_id"]
            last_references = headers["references"]
            last_sender = headers["from"]
            if not original_subject:
                original_subject = headers["subject"]

        record.state.to = parseaddr(last_sender)[1]
        record.state.in_reply_to_message_id = last_message_id
        record.state.references = (
            f"{last_references} {last_message_id}".strip() if last_references else last_message_id
        )

        result = composer.draft_reply(intent, context)
        record.state.subject = result.get("subject") or (f"Re: {original_subject}" if original_subject else "")
        record.state.body = result["body"]
        record.state.status = "awaiting_review"
    except Exception as exc:  # noqa: BLE001
        record.state.status = "error"
        record.state.error = str(exc)


async def run_send_draft(draft_id: str) -> None:
    record = get_draft(draft_id)
    try:
        result = gmail_client.send_message(
            gmail_service,
            to=record.state.to,
            subject=record.state.subject,
            body=record.state.body,
            thread_id=record.state.thread_id,
            in_reply_to_message_id=record.state.in_reply_to_message_id,
            references=record.state.references,
        )
        record.state.sent_message_id = result.get("id")
        record.state.status = "sent"
    except Exception as exc:  # noqa: BLE001
        record.state.status = "error"
        record.state.error = str(exc)


@app.post("/drafts/compose", response_model=StartDraftResponse, summary="Start a compose draft from intent")
async def post_compose(req: ComposeRequest, background_tasks: BackgroundTasks):
    draft_id = create_draft("compose", req.to)
    background_tasks.add_task(run_compose_draft, draft_id, req.intent)
    return StartDraftResponse(draft_id=draft_id, status="drafting")


@app.post("/drafts/reply", response_model=StartDraftResponse, summary="Start a reply draft for a thread")
async def post_reply(req: ReplyRequest, background_tasks: BackgroundTasks):
    draft_id = create_draft("reply", "", thread_id=req.thread_id)
    background_tasks.add_task(run_reply_draft, draft_id, req.thread_id, req.intent)
    return StartDraftResponse(draft_id=draft_id, status="drafting")


@app.get("/drafts/{draft_id}", response_model=EmailDraftState, summary="Poll draft state")
async def get_draft_endpoint(draft_id: str):
    record = get_draft(draft_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Draft '{draft_id}' not found.")
    return record.state


@app.patch("/drafts/{draft_id}", response_model=EmailDraftState, summary="Edit a draft awaiting review")
async def patch_draft(draft_id: str, req: DraftPatchRequest):
    record = get_draft(draft_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Draft '{draft_id}' not found.")
    if record.state.status != "awaiting_review":
        raise HTTPException(
            status_code=400, detail=f"Draft is not awaiting review (status={record.state.status})."
        )

    if req.to is not None:
        record.state.to = req.to
    if req.subject is not None:
        record.state.subject = req.subject
    if req.body is not None:
        record.state.body = req.body
    return record.state


@app.post("/drafts/{draft_id}/send", response_model=EmailDraftState, summary="Confirm and send a draft")
async def send_draft(draft_id: str, background_tasks: BackgroundTasks):
    record = get_draft(draft_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Draft '{draft_id}' not found.")
    if record.state.status != "awaiting_review":
        raise HTTPException(
            status_code=400, detail=f"Draft is not awaiting review (status={record.state.status})."
        )

    record.state.status = "sending"
    background_tasks.add_task(run_send_draft, draft_id)
    return record.state


@app.get("/inbox/unread", response_model=InboxUnreadResponse, summary="List unread messages with summaries")
async def get_inbox_unread(limit: int = 20):
    message_refs = gmail_client.list_unread(gmail_service, max_results=limit)
    items = []
    for ref in message_refs:
        full = gmail_client.get_message_full(gmail_service, ref["id"])
        headers = gmail_client.extract_headers(full)
        body = gmail_client.extract_plain_text_body(full)
        summary = composer.summarize_email(headers["from"], headers["subject"], body)
        items.append(
            InboxItem(
                message_id=ref["id"],
                thread_id=ref["threadId"],
                sender=headers["from"],
                subject=headers["subject"],
                date=headers["date"],
                summary=summary,
            )
        )
    return InboxUnreadResponse(items=items)


@app.get("/inbox/thread/{thread_id}", response_model=ThreadResponse, summary="Get full thread context")
async def get_inbox_thread(thread_id: str):
    thread = gmail_client.get_thread(gmail_service, thread_id)
    messages = []
    for msg in thread.get("messages", []):
        headers = gmail_client.extract_headers(msg)
        body = gmail_client.extract_plain_text_body(msg)
        messages.append(ThreadMessage(sender=headers["from"], date=headers["date"], body=body))
    return ThreadResponse(thread_id=thread_id, messages=messages)
