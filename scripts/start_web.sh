#!/usr/bin/env bash
# Render / Linux: apply migrations before serving (SQLite is not in git; build alone may skip migrate).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python manage.py migrate --noinput
exec gunicorn vunoh_assistant.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers 1 \
  --timeout 120 \
  --graceful-timeout 30
