from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

DraftStatus = Literal["drafting", "awaiting_review", "sending", "sent", "error"]
DraftMode = Literal["compose", "reply"]


class EmailDraftState(BaseModel):
    draft_id: str
    mode: DraftMode
    to: str
    subject: str = ""
    body: str = ""
    status: DraftStatus
    thread_id: Optional[str] = None
    in_reply_to_message_id: Optional[str] = None
    references: Optional[str] = None
    sent_message_id: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StartDraftResponse(BaseModel):
    draft_id: str
    status: DraftStatus


class ComposeRequest(BaseModel):
    to: str
    intent: str


class ReplyRequest(BaseModel):
    thread_id: str
    intent: str


class DraftPatchRequest(BaseModel):
    to: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None


class InboxItem(BaseModel):
    message_id: str
    thread_id: str
    sender: str
    subject: str
    date: str
    summary: str


class InboxUnreadResponse(BaseModel):
    items: list[InboxItem]


class ThreadMessage(BaseModel):
    sender: str
    date: str
    body: str


class ThreadResponse(BaseModel):
    thread_id: str
    messages: list[ThreadMessage]
