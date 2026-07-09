import asyncio
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import (  # noqa: E402
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)

import browser_session  # noqa: E402
import database  # noqa: E402
from field_scanner import scan_page  # noqa: E402
from filler import fill_and_submit  # noqa: E402
from mapper import map_fields  # noqa: E402
from models import (  # noqa: E402
    AnswerFieldRequest,
    FormField,
    FormRunState,
    ResumeUploadResponse,
    ReviewRequest,
    StartRunRequest,
    StartRunResponse,
)
from runs import create_run, finish_stream, get_run, push_step, run_queues  # noqa: E402

RESUME_DIR = database.RESUME_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    await browser_session.init_browser()
    yield
    await browser_session.close_browser()


app = FastAPI(
    title="Module 1 — Intelligent Form Filling",
    description="Generic any-site form detection, profile-driven autofill, and preview-before-submit.",
    version="1.0.0",
    lifespan=lifespan,
)


async def run_scan(run_id: str, url: str) -> None:
    record = get_run(run_id)
    try:
        await push_step(run_id, f"Navigating to {url}")
        page = await browser_session.new_page()
        record.page = page
        await page.goto(url, timeout=20000)

        await push_step(run_id, "Scanning page for form fields...")
        scan_result = await scan_page(page)
        await push_step(run_id, f"Found {len(scan_result.fields)} fields")

        profile = await database.get_profile()
        mapped_fields = map_fields(scan_result.fields, profile)

        record.frame_by_field_id = scan_result.frame_by_field_id
        record.submit_field_id = scan_result.submit_field_id
        record.state.fields = mapped_fields
        record.state.status = "awaiting_review"
        await push_step(run_id, "Ready for review.")
    except Exception as exc:  # noqa: BLE001
        record.state.status = "error"
        record.state.error = str(exc)
        await push_step(run_id, f"Error: {exc}")
        await finish_stream(run_id)


async def run_fill_and_submit(run_id: str) -> None:
    record = get_run(run_id)
    try:
        await push_step(run_id, "Submitting form...")
        await fill_and_submit(record.state.fields, record.frame_by_field_id, record.submit_field_id)
        record.state.status = "done"
        await push_step(run_id, "Form submitted successfully.")
    except Exception as exc:  # noqa: BLE001
        record.state.status = "error"
        record.state.error = str(exc)
        await push_step(run_id, f"Error: {exc}")
    finally:
        await finish_stream(run_id)


@app.post("/runs", response_model=StartRunResponse, summary="Start a form-fill run on a URL")
async def post_run(req: StartRunRequest, background_tasks: BackgroundTasks):
    run_id = create_run(req.url)
    background_tasks.add_task(run_scan, run_id, req.url)
    return StartRunResponse(run_id=run_id, status="scanning")


@app.get("/runs/{run_id}", response_model=FormRunState, summary="Get full run state incl. fields")
async def get_run_state(run_id: str):
    record = get_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return record.state


@app.websocket("/ws/runs/{run_id}")
async def ws_run(websocket: WebSocket, run_id: str):
    await websocket.accept()

    if run_id not in run_queues:
        await websocket.send_text("ERROR: unknown run_id")
        await websocket.close()
        return

    queue: asyncio.Queue = run_queues[run_id]
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


@app.post("/runs/{run_id}/answer", response_model=FormField, summary="Answer one missing field")
async def answer_field(run_id: str, req: AnswerFieldRequest):
    record = get_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    target = next((f for f in record.state.fields if f.field_id == req.field_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail=f"Field '{req.field_id}' not found in run.")

    target.proposed_value = req.value
    target.source = "answered"
    if target.mapped_key:
        await database.upsert_profile_fields({target.mapped_key: req.value})
    return target


@app.post("/runs/{run_id}/review", response_model=FormRunState, summary="Approve or reject the preview")
async def review_run(run_id: str, req: ReviewRequest, background_tasks: BackgroundTasks):
    record = get_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    if record.state.status != "awaiting_review":
        raise HTTPException(
            status_code=400, detail=f"Run is not awaiting review (status={record.state.status})."
        )

    value_by_id = {item.field_id: item.value for item in req.fields}
    for field in record.state.fields:
        if field.field_id in value_by_id:
            field.proposed_value = value_by_id[field.field_id]

    if req.action == "reject":
        record.state.status = "rejected"
        await push_step(run_id, "Run rejected by user.")
        await finish_stream(run_id)
        return record.state

    to_persist = {
        field.mapped_key: field.proposed_value
        for field in record.state.fields
        if field.mapped_key and field.proposed_value and field.element_type != "file"
    }
    await database.upsert_profile_fields(to_persist)

    record.state.status = "submitting"
    background_tasks.add_task(run_fill_and_submit, run_id)
    return record.state


@app.get("/user/profile", summary="Read the full profile")
async def get_profile_endpoint() -> dict[str, str]:
    return await database.get_profile()


@app.post("/user/profile", summary="Upsert one or more profile fields")
async def post_profile_endpoint(data: dict[str, str]) -> dict[str, str]:
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided to update.")
    await database.upsert_profile_fields(data)
    return await database.get_profile()


@app.post("/user/resume", response_model=ResumeUploadResponse, summary="Upload a resume PDF")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    dest_path = RESUME_DIR / f"{uuid.uuid4()}_{file.filename}"
    contents = await file.read()
    await asyncio.to_thread(dest_path.write_bytes, contents)
    await database.upsert_profile_fields({"resume_path": str(dest_path)})
    return ResumeUploadResponse(resume_path=str(dest_path))
