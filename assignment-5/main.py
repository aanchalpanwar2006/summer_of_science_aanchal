import asyncio
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, WebSocket, WebSocketDisconnect

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent / "assignment-4"))

from browser_tools import close_browser, init_browser  # noqa: E402

from agent_runner import run_agent  # noqa: E402
from database import get_profile, init_db, upsert_profile  # noqa: E402
from models import CommandRequest, CommandResponse, TaskStatus, UserProfile  # noqa: E402

tasks: dict[str, dict] = {}
task_queues: dict[str, asyncio.Queue] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_browser()
    yield
    await close_browser()


app = FastAPI(
    title="SOC Browser Agent API",
    description="FastAPI backend for the LangChain + Playwright browser agent.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/command", response_model=CommandResponse, summary="Submit a browser task command")
async def post_command(req: CommandRequest, background_tasks: BackgroundTasks):
    """
    Submit a natural-language command for the agent to execute.
    Returns a `task_id` you can poll via GET /status/{task_id}
    or stream live updates via WebSocket /ws/{task_id}.
    """
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "steps": [],
        "result": None,
    }
    task_queues[task_id] = asyncio.Queue()
    background_tasks.add_task(run_agent, task_id, req.command, tasks, task_queues)
    return CommandResponse(task_id=task_id)


@app.get("/status/{task_id}", response_model=TaskStatus, summary="Poll task progress")
async def get_status(task_id: str):
    """
    Returns the current status, list of steps taken, and final result (when done).
    Status values: pending | running | done | error
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return tasks[task_id]


@app.get("/user/profile", response_model=UserProfile, summary="Read user profile from SQLite")
async def get_user_profile():
    """Returns the stored user profile (name, email, phone, address, resume_text)."""
    return await get_profile()


@app.post("/user/profile", response_model=UserProfile, summary="Save or update user profile")
async def post_user_profile(profile: UserProfile):
    """
    Upserts the user profile in SQLite.
    Only provided fields are updated; omitted fields keep their current values.
    """
    data = profile.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided to update.")
    await upsert_profile(data)
    return await get_profile()


@app.websocket("/ws/{task_id}")
async def websocket_stream(websocket: WebSocket, task_id: str):
    """
    Stream live step-by-step updates for a running task.
    Each message is one agent step. Final message is '__DONE__'.
    """
    await websocket.accept()

    if task_id not in task_queues:
        await websocket.send_text("ERROR: unknown task_id")
        await websocket.close()
        return

    queue = task_queues[task_id]
    try:
        while True:
            msg = await queue.get()
            if msg is None:
                await websocket.send_text("__DONE__")
                break
            await websocket.send_text(msg)
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
