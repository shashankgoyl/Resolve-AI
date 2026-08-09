# Resolve AI — AI Customer Support Knowledge Agent

**Gmail → AI → Notion → Jira/GitHub → AI Decision → Human Approval → Resend**,
with every integration hop executed through **Swytchcode**.

Built for the buildathon brief: read customer support emails, classify and
research each one against internal knowledge and engineering trackers,
draft a reply, decide whether it's resolved / needs engineering / needs a
human / is insufficient to act on — and never send anything to a customer
without explicit human approval.

---

## Features

- **Full agent pipeline**: Gmail fetch → Gemini classification → Notion
  search → Jira search → GitHub search → Gemini decision → Gemini reply
  generation → conditional Jira ticket creation → human approval gate →
  Resend send. Every step is timed, logged, and rendered as a live
  **Agent Activity Timeline**.
- **Resolution Graph**: a visual Customer Issue → Knowledge → Evidence →
  AI Decision → Resolution → Response pipeline with a live confidence
  score, on every ticket.
- **Human-in-the-loop by design**: responses are always created as
  `pending_approval`. Nothing reaches a customer without **Approve & Send**
  (or an edit first). **Reject**, **Escalate**, and **Re-run AI** are all
  explicit, audited actions.
- **No hallucinated fixes**: if the evidence is insufficient or ambiguous
  (e.g. billing/refund cases), the agent returns `NEEDS_HUMAN_REVIEW` /
  `INSUFFICIENT_INFORMATION` instead of guessing.
- **Swytchcode as the sole integration layer**: one function,
  `SwytchcodeService.exec()`, is the only place that ever calls Gmail /
  Notion / Jira / GitHub / Resend. It resolves real canonical IDs from
  `tooling.json` and refuses to invent an endpoint it hasn't been told
  about.
- **Demo Mode**: 5 realistic sample tickets (failed payment, password
  reset, API 500s, stale plan limits, failing CSV export), fully working
  end to end with **zero external credentials**.
- **Full audit trail**: every AI action and every human decision is logged
  and viewable on the Audit Logs page.

---

## Project structure

```text
resolve-ai/
├── frontend/           React + TypeScript + Vite + Tailwind dashboard
├── backend/             FastAPI + Pydantic + Gemini + Swytchcode
├── supabase/            schema.sql + seed.sql
├── docs/architecture.md Mermaid architecture diagram + component notes
├── tooling.json         Swytchcode trusted-tool policy (placeholders)
├── README.md
└── DEMO.md              3–5 minute judging demo script
```

Frontend and backend are fully independent — separate installs, separate
run commands, separate deploys.

---

## Quickstart (Demo Mode — no credentials needed)

```bash
# backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # DEMO_MODE=true by default
uvicorn app.main:app --reload

# frontend (new terminal)
cd frontend
npm install
cp .env.example .env                # VITE_API_URL=http://localhost:8000
npm run dev
```

Open `http://localhost:5173`. You'll see the 5 demo tickets, a working
agent pipeline, and a "Demo mode" badge in the top bar. This was verified
to run end-to-end (backend `uvicorn` boot, all API routes, and
`npm run build`) while building this project.

---

## Supabase setup (for live/persistent mode)

1. Create a project at [supabase.com](https://supabase.com).
2. In the SQL editor, run `supabase/schema.sql`, then `supabase/seed.sql`
   if you want the same 5 demo tickets persisted as real rows.
3. From **Settings → API**, copy:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY` (**backend `.env`
     only — never in the frontend, never committed**)
4. Set `DEMO_MODE=false` in `backend/.env` once these are filled in and a
   ticket-ingestion path (see "Beyond this build" below) is wired up.

> The schema includes RLS policies for authenticated reads on every table.
> All writes go through the backend using the service-role key, which
> bypasses RLS by design — the frontend never talks to Supabase directly.

---

## Swytchcode setup

Swytchcode is the execution kernel between this backend and the real
Gmail / Notion / Jira / GitHub / Resend APIs — see `docs/architecture.md`
for how it's wired into the code. To go live:

```bash
# 1. Install the CLI
curl -fsSL https://cli.swytchcode.com/install.sh | sh    # macOS/Linux
irm https://cli.swytchcode.com/install.ps1 | iex          # Windows

# 2. Authenticate
swytchcode login

# 3. Initialize in the project root (creates .swytchcode/ + tooling.json)
swytchcode init

# 4. Register each integration your workspace has connected.
#    Use `swytchcode search <query>` or the Swytchcode dashboard to find
#    the REAL canonical IDs available to your account — they are not
#    hardcoded anywhere in this codebase on purpose.
swytchcode add gmail   <canonical_id_for_search_or_get_message>
swytchcode add notion  <canonical_id_for_page_search>
swytchcode add jira    <canonical_id_for_issue_search>
swytchcode add jira    <canonical_id_for_issue_create>
swytchcode add github  <canonical_id_for_issue_search>
swytchcode add resend  <canonical_id_for_send_email>

# 5. Inspect what you actually got
swytchcode info <canonical_id>
```

Then edit `tooling.json` at the project root and fill in
`resolve_ai_action_map` with the real canonical IDs, e.g.:

```json
"resolve_ai_action_map": {
  "gmail.get_message": "gmail.messages.get",
  "notion.search": "notion.pages.search",
  "jira.search_issues": "jira.issues.search",
  "jira.create_issue": "jira.issues.create",
  "github.search_issues": "github.issues.search",
  "resend.send_email": "resend.emails.send"
}
```

Set `SWYTCHCODE_API_KEY` and `DEMO_MODE=false` in `backend/.env`.
`backend/app/services/swytchcode_service.py` will then shell out to
`swytchcode exec <canonical_id> --json` for every integration call, with
timeouts, structured error capture, and full audit logging — and will
refuse to call anything not explicitly registered above.

---

## Gemini setup

1. Get a key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. Set `GEMINI_API_KEY` in `backend/.env`.
3. All three AI steps (`classify_email`, `decide_resolution`,
   `generate_reply` in `backend/app/services/gemini_service.py`) use
   Gemini's `response_schema` against Pydantic models — structured output,
   not parsed text.

**Never** put this key in the frontend or commit it — it's backend-only.

---

## Running the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`. Health check at
`GET /api/health` reports which of Supabase/Gemini/Swytchcode are
configured and whether the app is effectively running in demo mode.

## Running the frontend

```bash
cd frontend
npm install
npm run dev
```

Requires `VITE_API_URL` pointing at the backend (defaults to
`http://localhost:8000`).

---

## Deployment

### Frontend → Vercel / Netlify
- Build command: `npm run build` · Output directory: `dist`
- Environment variable: `VITE_API_URL=https://your-backend-url`

### Backend → Railway / Render / AWS
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables: everything in `backend/.env.example` —
  `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`,
  `SWYTCHCODE_API_KEY`, `DEMO_MODE=false`, `CORS_ORIGINS=https://your-frontend-url`
- Make sure the `swytchcode` CLI binary is available on the deploy image's
  `PATH` (or set `SWYTCHCODE_BIN` to its path) if running live.

### Database → Supabase
Already hosted — just run the migrations in `supabase/schema.sql` against
your project (SQL editor, or `supabase db push` if using the Supabase CLI).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Frontend loads but shows no tickets | Check `VITE_API_URL` matches where the backend is actually running, and check the backend terminal for CORS errors — add the frontend origin to `CORS_ORIGINS`. |
| `swytchcode: command not found` | Install the CLI (see Swytchcode setup) or set `SWYTCHCODE_BIN` to its absolute path. |
| A live integration call fails with "has no canonical_id in tooling.json" | You haven't run `swytchcode add` for that action yet, or haven't added the mapping to `resolve_ai_action_map`. This is intentional — the backend won't guess an endpoint. |
| Gemini calls fail in live mode | Confirm `GEMINI_API_KEY` is set and `DEMO_MODE=false`; check the Gemini API is enabled for your Google Cloud project. |
| Supabase writes fail | Confirm you're using the `service_role` key (not `anon`) in `SUPABASE_SERVICE_ROLE_KEY`, and that `supabase/schema.sql` has been applied. |

---

## How this maps to the judging criteria

- **Swytchcode API Integration (30%)** — every single Gmail/Notion/Jira/
  GitHub/Resend call in the codebase, with no exceptions, goes through
  `SwytchcodeService.exec()`. See `backend/app/services/swytchcode_service.py`
  and `integrations_service.py`. The Agent Activity Timeline surfaces the
  exact `canonical_id` and timing of every call so Swytchcode's role is
  visible, not incidental.
- **Technical Implementation (25%)** — typed end-to-end (Pydantic ↔
  TypeScript), structured Gemini output via `response_schema`, a real
  Postgres schema with RLS, an async orchestration pipeline with per-step
  timing/error capture, and a backend that was actually run and
  curl-tested (not just written) while building this.
- **Innovation (20%)** — the Resolution Graph (issue → knowledge →
  evidence → decision → resolution → response, with a live confidence
  ring) turns the agent's reasoning into something a judge can see at a
  glance, not just a log.
- **Functionality (10%)** — Demo Mode is a fully working product with zero
  external credentials: 5 realistic tickets, a real 9-step agent run per
  ticket, working approve/reject/escalate/re-run/create-Jira actions.
- **Real-World Impact (10%)** — the human-approval gate and the refusal to
  hallucinate a resolution (`NEEDS_HUMAN_REVIEW` /
  `INSUFFICIENT_INFORMATION`) are the difference between a toy demo and
  something a real support team could actually turn on.
- **UX (5%)** — a dedicated activity-timeline and resolution-graph visual
  language (not a generic admin template), consistent status color coding
  across every page, and one-click approve/edit/reject/escalate actions
  right where the evidence is.

---

## Beyond this build (honest scope notes)

A few things a production deployment would still need that are out of
scope for a buildathon backend:

- **Inbound Gmail ingestion**: this build's agent runs on tickets that
  already exist (the 5 demo fixtures, or rows already in
  `support_tickets`/`emails`). A production version would add a Gmail
  push-notification webhook (registered via `swytchcode exec` against the
  Gmail watch API) or a polling job that creates new tickets automatically.
- **Real canonical IDs**: as covered above, populating `tooling.json` with
  your workspace's actual Swytchcode canonical IDs is a manual step that
  requires your own `swytchcode login` session.
- **Auth**: `users`/Supabase Auth tables exist in the schema, but the
  frontend doesn't yet gate access behind a login screen.
