# Architecture: SOC Browser Agent System

## Overview
A full-stack browser automation system where a React UI accepts natural-language commands,
delegates them to a FastAPI backend, which runs a LangChain/LangGraph ReAct agent backed by
Playwright browser tools — streaming live progress back to the UI via WebSocket.

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        React UI                              │
│                   (assignment-6/ui)                          │
│                                                              │
│  ┌────────────────┐   POST /api/command                     │
│  │  Command Bar   │──────────────────────────────────►      │
│  └────────────────┘                                         │
│  ┌────────────────┐   WebSocket /ws/{task_id}               │
│  │  Activity Log  │◄─────────────────────────────────────   │
│  └────────────────┘                                         │
│  ┌────────────────┐   GET / POST /api/user/profile          │
│  │  Profile Page  │◄────────────────────────────────────►   │
│  └────────────────┘                                         │
└──────────────────────────────┬──────────────────────────────┘
                               │  HTTP + WebSocket
                               │  (proxied via Vite → :8000)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI Server  (assignment-5)                 │
│                                                              │
│  POST /command      →  generate task_id, queue background   │
│  GET  /status/{id}  →  poll task status + step list         │
│  WS   /ws/{id}      →  push step strings, send __DONE__     │
│  GET/POST /user/profile  →  SQLite profile CRUD             │
│                                                              │
│  SQLite (tasks.db): user_profile table                      │
└──────────────────────────────┬──────────────────────────────┘
                               │  asyncio background task
                               │  agent.astream_events()
                               ▼
┌─────────────────────────────────────────────────────────────┐
│         LangGraph ReAct AgentExecutor  (assignment-4)        │
│                                                              │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │     LLM     │  │  Browser Tools   │  │    Memory     │  │
│  │  gpt-4o-mini│  │  navigate_to()   │  │  MemorySaver  │  │
│  │  (OpenAI)   │  │  click_element() │  │  (per thread) │  │
│  │             │  │  type_text()     │  │               │  │
│  └─────────────┘  │  get_user_profile│  └───────────────┘  │
│                   └────────┬─────────┘                      │
└────────────────────────────┼────────────────────────────────┘
                             │  Playwright Chromium
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│                                                              │
│  • OpenAI API — LLM reasoning, tool-call decisions          │
│  • Target Websites — navigated/interacted via Chromium      │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

1. User types a command in **CommandBar** → `POST /api/command {"command": "..."}`
2. FastAPI returns `{task_id}` immediately (non-blocking)
3. UI opens **WebSocket** at `/ws/{task_id}`
4. Background task calls `agent.astream_events()` — each `on_tool_start` / `on_tool_end` event
   is pushed onto a per-task `asyncio.Queue`
5. WebSocket endpoint drains the queue and sends each step string to the UI
6. **ActivityLog** appends each message as it arrives; `__DONE__` sentinel closes the connection
7. `GET /status/{task_id}` can also be polled at any time for the full step history and final result

---

## Data Contracts (assignment-6/contracts.py)

| Model | Purpose |
|---|---|
| `UserProfile` | User identity stored in SQLite; used by agent's profile tool |
| `Task` | Lifecycle of one agent command (id, status, steps, result, timestamps) |
| `AgentAction` | Structured output of the intent parser — maps to browser tool calls |
