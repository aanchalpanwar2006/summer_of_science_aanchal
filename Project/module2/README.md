# Module 2 — Email Assistant

Draft, send, and reply to email from a one-sentence intent — an LLM writes
the subject/body, but nothing is ever sent without you explicitly reviewing
and confirming it. Also includes a read-only unread-inbox summary.

## Setup

### 1. Google Cloud OAuth (one-time, manual)

This module talks to your real Gmail account via the Gmail API, so you need
to create your own OAuth client — this can't be done on your behalf since it
requires your Google login.

1. Go to [console.cloud.google.com](https://console.cloud.google.com/),
   create or select a project.
2. **APIs & Services → Library** → search "Gmail API" → **Enable**.
3. **APIs & Services → OAuth consent screen**:
   - User type: **External**.
   - App name: anything (e.g. "Email Assistant Module 2"); use your own
     email as the support/developer contact.
   - **Test users**: add your own Gmail address — required while the app is
     in "Testing" status, or the consent screen will block you.
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Desktop app**.
   - Create, then **Download JSON**.
5. Rename the downloaded file to `credentials.json` and place it at
   `backend/storage/credentials.json`.
6. The first time you run the backend, a browser tab opens for one-time
   consent. After you approve, a `token.json` is cached next to
   `credentials.json` — no further manual steps unless scopes change or the
   token is revoked (see Troubleshooting below).

**Scopes requested** (least-privilege for this module): `gmail.send` +
`gmail.readonly` — enough for compose/send, thread-aware reply, and
inbox reading. We deliberately don't request `gmail.modify` since nothing
in this pass marks mail as read, labels, or deletes anything.

### 2. Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your OPENAI_API_KEY
# place credentials.json in backend/storage/ per step 1 above
uvicorn main:app --reload --port 8001
```

The API serves on `http://localhost:8001`. On first run it opens a browser
tab for Gmail consent.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite serves on its own port (prints the URL on start) and proxies `/api` to
the backend on port 8001.

## Using it

- **Compose tab**: enter a recipient and a one-sentence intent (e.g. "ask my
  professor for a deadline extension on the project"), click **Draft**. Once
  the LLM finishes, review/edit the subject and body, then click **Send**
  — nothing is sent until you click it.
- **Inbox tab**: shows your unread messages with a one-line summary each.
  Click **Reply** on any message to see the thread context, describe your
  reply's intent, draft it, review, and send — same review/confirm gate as
  Compose.

## Scope of this pass

Core slice: compose-from-intent → review/edit → explicit send; thread-aware
reply (correct `In-Reply-To`/`References`/`threadId` so it lands in the same
Gmail thread); read-only unread-inbox summary.

Deferred to a later pass (the architecture leaves room for these without a
rewrite): named contact groups / batch sends, scheduled send-later, saved
reusable templates, and auto-attaching the resume from Module 1's profile.

**Deliberate simplification**: drafting uses simple polling (`GET
/drafts/{id}` every ~800ms) rather than Module 1's WebSocket streaming —
drafting is one fast LLM call, not a multi-step process worth narrating live.

## Troubleshooting

- **"credentials.json not found"**: you skipped step 1 above, or placed the
  file somewhere other than `backend/storage/credentials.json`.
- **Consent screen blocks you / "app not verified"**: make sure your own
  Gmail address is added under **Test users** on the OAuth consent screen.
- **Token stopped working after working before**: you (or Google) revoked
  access. Delete `backend/storage/token.json` and restart the backend to
  re-trigger the consent flow.

## Tests

```bash
cd backend
pytest
```

These are unit tests only (mocked OpenAI client, mocked Gmail service) — no
live network calls, no real email sent. See `docs` in the parent plan for the
manual live-Gmail verification steps.
