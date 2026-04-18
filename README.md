# Vunoh AI Internship Practical Test — Diaspora Task Assistant

This repository is my submission for the **Vunoh Global AI Internship (2026)** practical test. It implements an AI-assisted web app that lets diaspora customers describe a need in plain English, then turns that into a **persisted task**: extracted intent and entities, **rule-based risk score**, **fulfillment steps**, **WhatsApp / email / SMS** drafts, **team assignment**, and a **dashboard** to track and update status.

The brief (problem, stack constraints, features, submission rules, and evaluation rubric) is supplied by Vunoh as **confidential applicant material** and is **not committed** in this repository—keep your copy private (for example in a local `docs/` folder that is gitignored). This README explains how to run the project, how it maps to that brief, and **why** key design choices were made.

---

## Tech stack (per brief)

| Layer    | Choice |
|----------|--------|
| Backend  | **Django** (Python) |
| Frontend | **HTML, CSS, vanilla JavaScript** (no frontend frameworks) |
| Database | **SQLite** (file `db.sqlite3`; suitable for local demo and submission dump) |
| AI       | **Google Gemini** via REST when configured; **deterministic heuristic fallback** when offline, in tests, or when the API errors (e.g. rate limits) |

---

## Quick start (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
# Edit `.env` with any settings your machine or host requires (file is gitignored).
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py runserver
```

Open **http://127.0.0.1:8000/** — the homepage includes the text input, JSON output from task creation, and the task dashboard.

---

## Mapping to the brief: features checklist

| # | Requirement (from PDF) | Implementation |
|---|------------------------|----------------|
| 1 | Plain-English customer input | Textarea on `/`; submits to task creation API |
| 2 | AI intent + structured entities | `POST /api/extract-intent/` and pipeline in `core/services/intent_extractor.py`. Intents: `send_money`, `get_airport_transfer`, `hire_service`, `verify_document`, `check_status` (snake_case in JSON/API). |
| 3 | Risk scoring (diaspora-grounded) + stored + visible | `core/services/risk_scorer.py`; stored on `Task.risk_score` / `risk_reasons`; shown in API, dashboard, and detail view |
| 4 | Task record: code, intent, entities, risk, status, timestamp | `core/models.py` — `Task` + related tables |
| 5 | AI-generated logical steps | Stored in `TaskStep`; from **one combined Gemini call** when enabled, else **intent-specific templates** in `task_creator.py` |
| 6 | Three channel messages (WhatsApp, email, SMS ≤160) | `TaskMessage`; same LLM/template path as steps; all three persisted |
| 7 | Employee category assignment + visible | `FINANCE`, `OPERATIONS`, `LEGAL`, `SUPPORT`; `assignment_reason` on task; rules + optional LLM when not using combined response |
| 8 | Dashboard: list tasks, show required fields, status buttons | Home page + `GET /api/tasks/`; status via `POST /api/tasks/<code>/status/` |
| 9 | Full persistence + SQL dump (≥5 sample tasks) | Migrations under `core/migrations/`; sample data: `python manage.py seed_sample_tasks --clear`; committed dump: [`sql/submission_sample.sql`](sql/submission_sample.sql) |

**Status history:** Every real status change appends a row to `TaskStatusHistory` (brief requires persistence; this gives an audit trail aligned with “when things go wrong” in the problem statement).

**Detail view:** `GET /api/tasks/<task_code>/` returns the full task including steps, all three messages, risk reasons, and customer text — so the UI can show everything the brief says must exist, not only what fits in the table.

---

## API reference

### `POST /api/extract-intent/`

```json
{ "request_text": "I need to send KES 15000 to my mother in Kisumu urgently." }
```

Returns `intent`, `entities`, `provider`, `fallback_used`, `risk_score`, `risk_reasons`.

### `POST /api/tasks/create/`

Same `request_text` body. Creates the full task graph and returns `task_code`, `steps`, `messages`, `assigned_team`, `assignment_reason`, `provider`, `fallback_used`, `llm_fulfillment_used`, `llm_assignment_used`, etc.

### `GET /api/tasks/`

Query params: `limit` (default 25, max 100), `offset` (pagination). Response includes `total`, `has_more`, and per-row `risk_reasons`.

### `GET /api/tasks/<task_code>/`

Full task payload for dashboard detail.

### `POST /api/tasks/<task_code>/status/`

```json
{ "status": "PENDING" | "IN_PROGRESS" | "COMPLETED" }
```

Persists change and records history when the status actually changes.

---

## Risk scoring (summary)

Scoring is **transparent and rule-based** (not a black-box model), so it can be defended in review. Starting from a base score, it adds or subtracts based on:

- **Intent** — e.g. money movement and document verification weigh higher than status checks.
- **Amount bands** — larger KES amounts increase score (thresholds at 15k / 50k / 100k).
- **Urgency** — high urgency adds pressure and error risk.
- **Recipient verification** — unverified recipient increases transfer risk when that signal is present in entities.
- **Document sensitivity** — land/title-type language increases document risk.
- **Customer history** — optional entity flags (e.g. returning customer, clean history) can reduce score when present.

Reasons are stored in `risk_reasons` and surfaced in the UI so the score is explainable, as the brief expects in the README and evaluation.

---

## Sample data and SQL submission file

Regenerate the dump after schema or seed changes:

```powershell
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py seed_sample_tasks --clear
.\.venv\Scripts\python manage.py export_sqlite_dump sql/submission_sample.sql
```

The committed [`sql/submission_sample.sql`](sql/submission_sample.sql) contains the schema and **five** fully populated tasks (entities, steps, three messages, risk, assignment, mixed statuses and history).

---

## Submission notes (PDF)

- **GitHub:** This repo is intended to contain all source, a clear layout (`vunoh_assistant/`, `core/`, `templates/`, `static/`, `sql/`), and this README.
- **SQL dump:** Included at `sql/submission_sample.sql` as required.
- **Hosted demo:** Optional; not required for a passing submission per the brief.

Exact **Day 1 / Final form URLs and deadlines** are in the PDF (EAT times, 2026). Use the links or instructions Vunoh provides with the brief.

---

## Decisions I made and why

This section is required by the brief: using AI tools is fine; **not** being able to explain the result is not.

### Which AI tools I used and for what

- **Cursor (and LLM assistance)** — scaffolding, refactors, tests, and documentation while I kept ownership of architecture and behavior. I treated suggestions as drafts: I traced every path in Django (views → services → models) and adjusted when something didn’t match the brief or the database schema.
- **Google Gemini** — optional “AI brain” for intent shaping and for **one structured JSON response** on task create (intent, entities, team, steps, and three messages) when the remote model is enabled in configuration. When Gemini is unavailable or returns errors, **heuristics and templates** keep the app runnable and testable.

### How I designed the prompts (and what I deliberately excluded)

- **Intent extraction prompt** (`intent_extractor.py`) — Ask for **only JSON**: allowed intent enum and a **flat** `entities` object. I excluded narrative prose, markdown fences, and nested structures so parsing stays predictable. Unknown fields are discouraged; consistency matters more than creative copy at this layer.
- **Combined task prompt** (`llm_combined_task.py`) — Single response that must include intent, entities, `assigned_team`, `assignment_reason`, `steps` (4–7 strings), and `whatsapp` / `email` / `sms` with the **real task code** embedded. I excluded letting the model invent extra keys or channels so validation stays strict and all rows fit the existing schema.
- **What I excluded globally** — Letting the LLM choose open-ended statuses, teams outside the four categories, or unconstrained step counts. Those would break DB constraints and the dashboard; the model is constrained to **our** task model, not the other way around.

### One decision where I overrode a default suggestion

- **Default Gemini model name** — Early defaults used `gemini-1.5-flash`, which started returning **404** against the current `generativelanguage.googleapis.com` endpoint. I moved the default to **`gemini-2.0-flash`** in code instead of blindly trusting an older tutorial string. That’s a small change but it’s the difference between “works” and “mysteriously broken” for reviewers running the repo.

### One thing that didn’t work as expected and how I fixed it

- **Quota / 429 from Gemini** — With a free-tier key, `generateContent` often returned **429 Too Many Requests**. The app still had to **work** and stay demoable. I implemented two layers: (1) **combined task creation** = one HTTP call instead of three when Gemini is on, to stay under limits; (2) on failure, **heuristic extraction + rule-based assignment + template steps/messages**, and when combined fails, **no extra** follow-up Gemini calls for assignment/fulfillment so we don’t burn quota on a doomed path. Tests and offline use rely on the same fallbacks.

### Risk scoring and assignment philosophy

- **Risk** stays **rule-based** so every point is explainable in the README and in `risk_reasons`, matching the evaluation weight on diaspora context and documentation.
- **Assignment** has explicit routing rules (money → Finance, documents → Legal, etc.) so behavior is predictable; LLM assignment is an optional enhancement when not already supplied by the combined JSON.

---

## Tests

```powershell
.\.venv\Scripts\python manage.py test core.tests
```
