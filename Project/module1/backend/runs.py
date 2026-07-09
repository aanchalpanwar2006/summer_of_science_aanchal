import asyncio
import uuid
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import Frame, Page

from models import FormRunState

runs: dict[str, "RunRecord"] = {}
run_queues: dict[str, asyncio.Queue] = {}


@dataclass
class RunRecord:
    state: FormRunState
    page: Optional[Page] = None
    frame_by_field_id: Optional[dict[str, Frame]] = None
    submit_field_id: Optional[str] = None


def create_run(url: str) -> str:
    run_id = str(uuid.uuid4())
    runs[run_id] = RunRecord(state=FormRunState(run_id=run_id, url=url, status="scanning"))
    run_queues[run_id] = asyncio.Queue()
    return run_id


def get_run(run_id: str) -> Optional[RunRecord]:
    return runs.get(run_id)


async def push_step(run_id: str, message: str) -> None:
    queue = run_queues.get(run_id)
    if queue is not None:
        await queue.put(message)


async def finish_stream(run_id: str) -> None:
    queue = run_queues.get(run_id)
    if queue is not None:
        await queue.put(None)
