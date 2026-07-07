from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    resume_text: str | None = None
    resume_path: str | None = None


class Task(BaseModel):
    task_id: str
    command: str
    status: Literal["pending", "running", "done", "error"] = "pending"
    steps: list[str] = Field(default_factory=list)
    result: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None


class AgentAction(BaseModel):
    action: Literal["navigate", "fill_form", "email", "summarize", "click", "clarify"]
    target_url: str | None = None
    data: dict[str, str] = Field(default_factory=dict)
    steps: list[str] = Field(default_factory=list)
    question: str | None = None
