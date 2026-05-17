from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS generation_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     TEXT UNIQUE NOT NULL,
    jd_text     TEXT NOT NULL,
    template    TEXT DEFAULT 'professional',
    status      TEXT NOT NULL,
    elapsed_ms  INTEGER,
    resume_id   TEXT,
    gap_report  TEXT,
    error       TEXT,
    created_at  TEXT NOT NULL,
    completed_at TEXT
);
"""


class HistoryRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_conn() as conn:
            conn.executescript(SCHEMA_SQL)

    def add_record(
        self,
        task_id: str,
        jd_text: str,
        status: str,
        template: str = "professional",
        elapsed_ms: int | None = None,
        resume_id: str | None = None,
        gap_report: dict | None = None,
        error: str | None = None,
    ) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        completed_at = created_at if status in ("completed", "failed", "not_viable") else None
        with self._get_conn() as conn:
            cur = conn.execute(
                """INSERT INTO generation_history
                   (task_id, jd_text, template, status, elapsed_ms, resume_id,
                    gap_report, error, created_at, completed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task_id,
                    jd_text,
                    template,
                    status,
                    elapsed_ms,
                    resume_id,
                    json.dumps(gap_report, ensure_ascii=False) if gap_report else None,
                    error,
                    created_at,
                    completed_at,
                ),
            )
            return cur.lastrowid

    def list_records(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT id, task_id, jd_text, template, status, elapsed_ms,
                          resume_id, gap_report, error, created_at, completed_at
                   FROM generation_history
                   ORDER BY id DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()

        records = []
        for row in rows:
            d = dict(row)
            if d["gap_report"]:
                d["gap_report"] = json.loads(d["gap_report"])
            # Check if resume file still exists on disk (for download ability)
            if d["resume_id"]:
                from iresume.config import settings
                filepath = settings.resumes_dir / f"{d['resume_id']}.md"
                d["file_exists"] = filepath.exists()
            records.append(d)
        return records

    def get_record(self, task_id: str) -> dict[str, Any] | None:
        with self._get_conn() as conn:
            row = conn.execute(
                """SELECT id, task_id, jd_text, template, status, elapsed_ms,
                          resume_id, gap_report, error, created_at, completed_at
                   FROM generation_history WHERE task_id = ?""",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        d = dict(row)
        if d["gap_report"]:
            d["gap_report"] = json.loads(d["gap_report"])
        if d["resume_id"]:
            from iresume.config import settings
            filepath = settings.resumes_dir / f"{d['resume_id']}.md"
            d["file_exists"] = filepath.exists()
        return d

    def delete_record(self, task_id: str) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM generation_history WHERE task_id = ?",
                (task_id,),
            )
            return cur.rowcount > 0

    def count(self) -> int:
        with self._get_conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM generation_history").fetchone()[0]
