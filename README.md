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

## Project status
- Step 1 complete: runnable skeleton + homepage UI scaffold.
- Step 2 complete: persistence schema + admin visibility for tasks and related objects.
- Step 3 in progress: structured intent/entities extraction endpoint + UI output panel.

## Decisions I made and why (to be completed)
- Which AI tools I used and where
- How I designed the system prompt
- One override decision and why
- One unexpected failure and how I resolved it

