from pydantic import BaseModel


class CommandRequest(BaseModel):
    command: str


class CommandResponse(BaseModel):
    task_id: str
    status: str = "pending"


class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending | running | done | error
    steps: list[str]
    result: str | None = None


class UserProfile(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    resume_text: str | None = None
