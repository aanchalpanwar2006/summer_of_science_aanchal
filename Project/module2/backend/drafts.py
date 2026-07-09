import uuid
from dataclasses import dataclass
from typing import Optional

from models import DraftMode, EmailDraftState

drafts: dict = {}


@dataclass
class DraftRecord:
    state: EmailDraftState


def create_draft(mode: DraftMode, to: str, thread_id: Optional[str] = None) -> str:
    draft_id = str(uuid.uuid4())
    drafts[draft_id] = DraftRecord(
        state=EmailDraftState(draft_id=draft_id, mode=mode, to=to, status="drafting", thread_id=thread_id)
    )
    return draft_id


def get_draft(draft_id: str) -> Optional[DraftRecord]:
    return drafts.get(draft_id)
