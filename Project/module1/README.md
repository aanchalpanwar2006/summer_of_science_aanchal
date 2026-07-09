# Module 1 — Intelligent Form Filling

Generic, any-site form filler: scans a page (including iframes) for fillable
fields, maps them to a saved profile, asks for anything missing, and always
shows a full preview before it ever clicks submit.

## Setup

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # then add your OPENAI_API_KEY
uvicorn main:app --reload
```

The API serves on `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite serves on `http://localhost:5173` and proxies `/api` and `/ws` to the
backend on port 8000.

## Using it

1. Open the **Profile** tab and fill in whatever you already know about
   yourself (name, email, phone, etc.) and upload a resume PDF.
2. Switch to **Form Fill**, paste a form URL (e.g.
   `https://demoqa.com/automation-practice-form`), and click **Scan**.
3. Once scanning finishes, review every detected field. Fields the agent
   couldn't match to your profile are flagged **Missing** — fill them in and
   click **Save answer** (this is saved to your profile immediately, whether
   or not you go on to submit the form).
4. Click **Approve & Submit** to actually fill and submit the page, or
   **Reject** to discard the run without touching the page.

## Scope of this pass

This is the core slice of Module 1: generic field detection (incl. iframes),
profile-driven autofill, missing-field Q&A that persists to the profile,
full preview/edit/approve/reject before submit, and resume upload.

Deferred to a later pass (the architecture leaves room for these without a
rewrite): LLM-generated long-form answers (SOP/"why this role" text), saved
response templates, native Google Forms-specific handling, a
screenshot-to-vision fallback for unusual layouts, and automatic retry on
validation errors.

**Known limitation**: detection targets standard HTML form elements
(`input`, `textarea`, `select`, checkboxes, radios, file inputs). Custom
JS-only widgets that don't use real `<select>`/`<input>` elements (e.g.
`react-select` dropdowns) aren't picked up yet.

## Tests

```bash
cd backend
pytest
```

See `docs/architecture.md` for the full data flow.
