# DEMO.md — 3–5 minute judging walkthrough

Runs entirely in **Demo Mode** — no external credentials required. Start both
servers (see README) and open `http://localhost:5173`.

---

### 0:00 – 0:30 · Dashboard
Land on the **Dashboard**. Point out the live stats (total tickets, AI
resolved, open, escalations, avg resolution time, resolution rate) and the
sentiment breakdown chart. Say:

> "This is Resolve AI — every ticket here came in as a real customer email
> and was worked by an autonomous agent, end to end, through Swytchcode."

### 0:30 – 1:15 · Inbox → an easy win
Click **Inbox**. Open ticket **RES-1002** ("Password reset link not
working"). The agent run fires live:

- Point at the **Agent Activity Timeline** on the right — each row is one
  `swytchcode exec <canonical_id>` call: Gmail fetch, AI classify, Notion
  search, Jira search, GitHub search, AI decide, generate reply — with real
  timings and statuses.
- Point at the **Resolution Graph** at the top: Customer Issue → Knowledge →
  Evidence → AI Decision → Resolution → Response, with the confidence ring.
- Show the drafted reply (it found the exact Notion KB article about the
  stale session cookie) and the `RESOLVED` decision at 91% confidence.
- Click **Approve & Send** — the response status flips to `sent`, and this
  fires `resend.send_email` through Swytchcode.

### 1:15 – 2:15 · A bug that needs engineering
Open ticket **RES-1005** ("CSV export keeps failing at 80%"). Walk the same
timeline, but this time:

- Notion has a partial match (export size limits) but no confirmed fix.
- Jira/GitHub search surfaces a related open issue.
- The AI decides `NEEDS_ENGINEERING` and — because no existing ticket
  covers this exact failure — **creates a new Jira ticket automatically**
  (watch it appear in the timeline: `jira.create` → `ENG-4901`).
- The drafted reply tells the customer it's been escalated, honestly,
  without promising a fix that doesn't exist yet.
- Click **Edit Response**, tweak a sentence, **Save & Send** — showing the
  human-in-the-loop edit path.

### 2:15 – 3:00 · A case that needs a human — no hallucination
Open ticket **RES-1001** ("Payment failed but money was deducted"). The
agent finds a KB article about pending holds, but this touches real money —
the decision is `NEEDS_HUMAN_REVIEW`, not a guessed resolution. Click
**Escalate** and show it land in the **Audit Logs** page as a fully
attributed human action. Say:

> "This is the guardrail — the agent never invents a refund or a fix it
> can't back with evidence. If knowledge is insufficient, it asks a human."

### 3:00 – 3:45 · Integrations & audit trail
Click **Integrations** — show Gmail / Notion / Jira / GitHub / Resend /
Swytchcode all reporting status (Demo mode here; `connected` once real
credentials are wired up). Click **Audit Logs** — scroll the full trail:
every AI action and every human action, attributed and timestamped.

### 3:45 – 4:30 · Under the hood (for judges scoring Swytchcode integration)
Open `backend/app/services/swytchcode_service.py` and
`backend/app/services/integrations_service.py`. Point out:

- Every external call goes through one function: `SwytchcodeService.exec()`.
- It resolves canonical IDs from `tooling.json` — nothing is hardcoded or
  invented; if a tool isn't registered, the call fails loudly instead of
  guessing an endpoint.
- Show `tooling.json` at the project root and the `swytchcode add` commands
  in the README for wiring up real Gmail/Notion/Jira/GitHub/Resend access.

### 4:30 – 5:00 · Close
> "Gmail in, AI in the middle, Notion/Jira/GitHub as evidence, a human
> always in the loop before anything reaches a customer, Resend out — and
> every single hop, real or demo, executed and logged through Swytchcode."

---

### Fallback timings if you're short on time
- **Cut**: the "under the hood" code walkthrough (3:45–4:30) — the
  Integrations page conveys the same point visually.
- **Keep**: one RESOLVED ticket, one NEEDS_ENGINEERING ticket (Jira
  creation is the most visually interesting), and the Audit Logs page.
