from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

ElementType = Literal[
    "text", "email", "tel", "date", "number", "textarea", "select", "checkbox", "radio", "file", "other"
]
FieldSource = Literal["profile", "answered", "missing"]
RunStatus = Literal["scanning", "awaiting_review", "submitting", "done", "error", "rejected"]


class FieldOption(BaseModel):
    value: str
    label: str


class FormField(BaseModel):
    field_id: str
    label: str
    element_type: ElementType
    required: bool = False
    options: list[FieldOption] = Field(default_factory=list)
    current_value: str = ""
    proposed_value: str = ""
    mapped_key: Optional[str] = None
    source: FieldSource = "missing"


class FormRunState(BaseModel):
    run_id: str
    url: str
    status: RunStatus
    fields: list[FormField] = Field(default_factory=list)
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StartRunRequest(BaseModel):
    url: str


class StartRunResponse(BaseModel):
    run_id: str
    status: RunStatus


class AnswerFieldRequest(BaseModel):
    field_id: str
    value: str


class ReviewFieldValue(BaseModel):
    field_id: str
    value: str


class ReviewRequest(BaseModel):
    fields: list[ReviewFieldValue]
    action: Literal["approve", "reject"]


class ResumeUploadResponse(BaseModel):
    resume_path: str
