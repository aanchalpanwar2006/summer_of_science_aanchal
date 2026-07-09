# Architecture: Module 1 — Intelligent Form Filling

## Overview

A React UI submits a URL to scan. A FastAPI backend drives a Playwright
Chromium instance to deterministically detect every fillable field on the
page (including inside iframes), maps each field to the user's saved
profile, and presents a full preview back to the UI. Nothing is written to
the live page, and no submit button is clicked, until the user explicitly
approves. Field detection and filling are plain deterministic code — the
LLM is only used as a narrow, batched fallback when a field's label can't be
matched to a profile key by exact/alias/fuzzy matching.

## System Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        React UI (frontend/)                   │
│  ┌────────────┐  POST /api/runs           ┌────────────────┐ │
│  │  UrlBar    │─────────────────────────► │  FormPreview   │ │
│  └────────────┘                           │  (edit/answer/ │ │
│  ┌────────────┐  WS /ws/runs/{id}         │  approve/      │ │
│  │ ActivityLog│◄───────────────────────── │  reject)       │ │
│  └────────────┘                           └────────┬───────┘ │
│  ┌────────────┐  GET/POST /api/user/profile         │        │
│  │ ProfilePage│◄────────────────────────────────────┘        │
│  └────────────┘  POST /api/user/resume                       │
└───────────────────────────┬────────────────────────────────--┘
                             │ HTTP + WebSocket (Vite proxy → :8000)
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                  FastAPI backend (backend/main.py)             │
│                                                                │
│  POST /runs                → create run, scan in background   │
│  GET  /runs/{id}            → full run state + fields         │
│  WS   /ws/runs/{id}         → live scan/fill progress          │
│  POST /runs/{id}/answer     → answer one missing field         │
│  POST /runs/{id}/review     → approve (fill+submit) or reject  │
│  GET/POST /user/profile     → EAV profile CRUD (database.py)   │
│  POST /user/resume          → store resume PDF                 │
└───────────────────────────┬────────────────────────────────--┘
                             │
        ┌────────────────────┼─────────────────────────┐
        ▼                    ▼                          ▼
┌───────────────┐   ┌──────────────────┐      ┌──────────────────┐
│ field_scanner  │   │      mapper       │      │      filler       │
│ deterministic  │   │ exact→alias→fuzzy │      │ re-locate tagged  │
│ DOM walk incl. │──►│ →batched LLM      │─────►│ elements, fill,    │
│ iframes, tags  │   │ fallback          │      │ click submit       │
│ elements with  │   │ (openai, 1 call/  │      │                    │
│ data-agent-    │   │ run, only for     │      │                    │
│ field-id       │   │ unresolved)       │      │                    │
└───────┬────────┘   └──────────────────┘      └──────────────────┘
        │                                                 │
        ▼                                                 ▼
┌────────────────────────────────────────────────────────────────┐
│              Playwright Chromium (browser_session.py)           │
│                    target website under test                    │
└────────────────────────────────────────────────────────────────┘
```

## Data flow

1. User submits a URL → `POST /runs` creates an in-memory `RunRecord`
   (`runs.py`) and schedules `run_scan` as a background task; returns
   `run_id` immediately.
2. `run_scan` navigates to the URL, calls `field_scanner.scan_page`, which
   walks every frame's DOM in one `frame.evaluate()` call each, tagging
   every fillable element with a `data-agent-field-id` attribute (the tag
   *is* the locator — no CSS selector is ever reconstructed after the fact).
3. `mapper.map_fields` resolves each detected label to a profile key via
   exact → alias → fuzzy matching; anything still unresolved is sent in a
   single batched OpenAI call. Fields with a profile hit get
   `source="profile"`; fields still unresolved get `source="missing"`.
4. Run status becomes `awaiting_review`; the UI polls `GET /runs/{id}` and
   renders every field — editable inline, missing ones flagged.
5. `POST /runs/{id}/answer` lets the user fill in a missing field; the
   answer is persisted to the profile **immediately**, independent of the
   run's eventual outcome.
6. `POST /runs/{id}/review` with `action=approve` persists all final values
   to the profile, then schedules `run_fill_and_submit`, which re-locates
   each tagged element via its stored `Frame` reference and applies the
   right Playwright action per element type, then clicks the tagged submit
   button. `action=reject` ends the run without touching the page.

## Data contracts (`backend/models.py`)

| Model | Purpose |
|---|---|
| `FormField` | One detected field: label, type, options, current/proposed value, mapped profile key, source |
| `FormRunState` | Full lifecycle of one scan→review→submit run |
| `StartRunRequest` / `StartRunResponse` | `POST /runs` payload |
| `AnswerFieldRequest` | `POST /runs/{id}/answer` payload |
| `ReviewRequest` | `POST /runs/{id}/review` payload |

## Profile storage (`backend/database.py`)

A single EAV table (`profile_fields(key, value, updated_at)`) instead of a
fixed-column schema, so the profile can grow arbitrary keys over time — every
new field learned from a form becomes a new row, no migration needed. The
resume path is stored as an ordinary key (`resume_path`), not a special case.
