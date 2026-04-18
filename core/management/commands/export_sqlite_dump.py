from __future__ import annotations

import sqlite3

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Write a SQL dump of the default SQLite database (schema + data) to a file."

    def add_arguments(self, parser):
        parser.add_argument(
            "output",
            nargs="?",
            default="sql/submission_sample.sql",
            help="Output path for the SQL dump (default: sql/submission_sample.sql).",
        )

    def handle(self, *args, **options):
        db_path = settings.DATABASES["default"]["NAME"]
        out_path = options["output"]
        conn = sqlite3.connect(str(db_path))
        try:
            lines = list(conn.iterdump())
        finally:
            conn.close()

        with open(out_path, "w", encoding="utf-8") as handle:
            for line in lines:
                handle.write(line + "\n")

        self.stdout.write(self.style.SUCCESS(f"Wrote SQL dump to {out_path} ({len(lines)} statements)."))
