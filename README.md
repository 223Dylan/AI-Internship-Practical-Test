# Vunoh AI Internship Practical Test (2026)

AI-powered assistant for Kenyans abroad to initiate and track requests for money transfers, local services, and document verification.

## Tech stack
- Backend: Django (Python)
- Frontend: HTML + CSS + vanilla JavaScript (no frontend frameworks)
- DB: SQLite (local dev)

## Setup (Windows / PowerShell)

Create a virtualenv and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Create your environment file:

```bash
copy .env.example .env
```

Run migrations and start the server:

```bash
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py runserver
```

Open the app at `http://127.0.0.1:8000/`.

## Intent extraction API (Step 3)
- Endpoint: `POST /api/extract-intent/`
- Request body:

```json
{ "request_text": "I need to send KES 15000 to my mother in Kisumu urgently." }
```

- Example PowerShell call:

```bash
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/extract-intent/ `
  -ContentType "application/json" `
  -Body '{"request_text":"Please verify my land title deed for Karen"}'
```

- Provider behavior:
  - `AI_PROVIDER=gemini` + `AI_API_KEY=<key>` uses Gemini extraction
  - otherwise falls back to deterministic mock extraction to keep the app testable offline

## Risk scoring (Step 4)
- Risk scoring is now computed for each extraction response and returned as:
  - `risk_score` (0-100)
  - `risk_reasons` (human-readable explanation list)
- Current scoring factors include:
  - intent type risk uplift
  - amount thresholds
  - urgency
  - recipient verification signal
  - document sensitivity (e.g. land/title)
  - returning customer with clean history risk reduction

## Task creation + listing APIs (Step 5)
- Create endpoint: `POST /api/tasks/create/`
  - runs extraction + risk scoring
  - creates a persisted task with unique code
  - stores normalized entity key-value rows
  - writes initial status history (`PENDING -> PENDING`)
- List endpoint: `GET /api/tasks/?limit=20`
  - returns recent tasks with code, intent, status, risk, assignment, and created time

## Step + message generation (Step 6)
- `POST /api/tasks/create/` now also:
  - generates intent-specific fulfillment steps and stores them in `TaskStep`
  - generates and stores channel-specific messages in `TaskMessage`
    - WhatsApp style
    - Email style
    - SMS style (<=160 chars)
- The create response now includes `steps` and `messages` arrays for immediate validation.

## Employee assignment (Step 7)
- Team assignment is now handled by dedicated routing logic in `employee_assigner`.
- Assignment uses intent and context hints to map tasks to:
  - `FINANCE` for money transfer
  - `OPERATIONS` for service/airport execution
  - `LEGAL` for document verification
  - `SUPPORT` for status follow-up/default routing
- `POST /api/tasks/create/` includes:
  - `assigned_team`
  - `assignment_reason`

## Task dashboard + status updates (Step 8)
- Home page dashboard lists recent tasks (code, intent, status, risk, team, created time).
- Each row has **Pending**, **In progress**, and **Completed** actions; each click calls:
  - `POST /api/tasks/<task_code>/status/` with body `{ "status": "PENDING" | "IN_PROGRESS" | "COMPLETED" }`
- Updates persist immediately on `Task` and append a row to `TaskStatusHistory` when the status actually changes.

## Project status
- Step 1 complete: runnable skeleton + homepage UI scaffold.
- Step 2 complete: persistence schema + admin visibility for tasks and related objects.
- Step 3 complete: structured intent/entities extraction endpoint + UI output panel.
- Step 4 complete: deterministic diaspora-aware risk scoring engine and API output.
- Step 5 complete: task creation pipeline + API dashboard listing.
- Step 6 complete: step generation + three-format message persistence.
- Step 7 complete: explicit employee assignment routing and rationale exposure.
- Step 8 complete: dashboard UI + immediate status updates with history.

## Decisions I made and why (to be completed)
- Which AI tools I used and where
- How I designed the system prompt
- One override decision and why
- One unexpected failure and how I resolved it

