"""SQLite data access for bookings and call analytics."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


class DataStore:
    """Simple SQLite-backed store for admin/reporting data."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    booking_type TEXT NOT NULL,
                    parent_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    child_name TEXT NOT NULL,
                    start_time_utc TEXT NOT NULL,
                    end_time_utc TEXT NOT NULL,
                    status TEXT NOT NULL,
                    estimated_revenue REAL NOT NULL DEFAULT 0,
                    google_event_id TEXT,
                    google_event_link TEXT,
                    reminder_id TEXT,
                    metadata_json TEXT,
                    created_at_utc TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS call_logs (
                    call_id TEXT PRIMARY KEY,
                    session_id TEXT UNIQUE NOT NULL,
                    customer_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    started_at_utc TEXT NOT NULL,
                    ended_at_utc TEXT NOT NULL,
                    duration_seconds REAL NOT NULL DEFAULT 0,
                    user_turns INTEGER NOT NULL DEFAULT 0,
                    assistant_turns INTEGER NOT NULL DEFAULT 0,
                    first_user_utterance TEXT,
                    first_assistant_utterance TEXT,
                    transcript_json TEXT,
                    created_at_utc TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def insert_booking(
        self,
        *,
        customer_id: str,
        booking_type: str,
        parent_name: str,
        phone_number: str,
        child_name: str,
        start_time_utc: str,
        end_time_utc: str,
        status: str,
        estimated_revenue: float,
        google_event_id: str | None = None,
        google_event_link: str | None = None,
        reminder_id: str | None = None,
        metadata: Dict[str, Any] | None = None,
        booking_id: str | None = None,
    ) -> str:
        booking_id = booking_id or str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO bookings (
                    booking_id, customer_id, booking_type, parent_name, phone_number, child_name,
                    start_time_utc, end_time_utc, status, estimated_revenue,
                    google_event_id, google_event_link, reminder_id, metadata_json, created_at_utc
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    booking_id,
                    customer_id,
                    booking_type,
                    parent_name,
                    phone_number,
                    child_name,
                    start_time_utc,
                    end_time_utc,
                    status,
                    float(estimated_revenue or 0),
                    google_event_id,
                    google_event_link,
                    reminder_id,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
        return booking_id

    def list_bookings(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM bookings
                ORDER BY start_time_utc DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def insert_call_log(
        self,
        *,
        session_id: str,
        customer_id: str,
        channel: str,
        started_at_utc: str,
        ended_at_utc: str,
        duration_seconds: float,
        user_turns: int,
        assistant_turns: int,
        first_user_utterance: str | None,
        first_assistant_utterance: str | None,
        transcript: List[Dict[str, Any]],
    ) -> str:
        call_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO call_logs (
                    call_id, session_id, customer_id, channel, started_at_utc, ended_at_utc,
                    duration_seconds, user_turns, assistant_turns, first_user_utterance,
                    first_assistant_utterance, transcript_json, created_at_utc
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id,
                    session_id,
                    customer_id,
                    channel,
                    started_at_utc,
                    ended_at_utc,
                    float(duration_seconds or 0),
                    int(user_turns or 0),
                    int(assistant_turns or 0),
                    first_user_utterance,
                    first_assistant_utterance,
                    json.dumps(transcript, ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
        return call_id

    def list_calls(self, limit: int = 300) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM call_logs
                ORDER BY started_at_utc DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def summary(self, days: int = 30) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=max(days, 1))
        since_iso = since.isoformat()

        with self._connect() as conn:
            total_bookings = conn.execute("SELECT COUNT(*) AS c FROM bookings").fetchone()["c"]
            total_revenue = conn.execute(
                "SELECT COALESCE(SUM(estimated_revenue), 0) AS s FROM bookings"
            ).fetchone()["s"]
            bookings_window = conn.execute(
                "SELECT COUNT(*) AS c FROM bookings WHERE created_at_utc >= ?",
                (since_iso,),
            ).fetchone()["c"]
            revenue_window = conn.execute(
                "SELECT COALESCE(SUM(estimated_revenue), 0) AS s FROM bookings WHERE created_at_utc >= ?",
                (since_iso,),
            ).fetchone()["s"]
            calls_window = conn.execute(
                "SELECT COUNT(*) AS c FROM call_logs WHERE created_at_utc >= ?",
                (since_iso,),
            ).fetchone()["c"]
            revenue_daily_rows = conn.execute(
                """
                SELECT substr(start_time_utc, 1, 10) AS day, COALESCE(SUM(estimated_revenue), 0) AS revenue,
                       COUNT(*) AS bookings
                FROM bookings
                WHERE start_time_utc >= ?
                GROUP BY substr(start_time_utc, 1, 10)
                ORDER BY day ASC
                """,
                (since_iso,),
            ).fetchall()

        daily = [dict(r) for r in revenue_daily_rows]
        conversion_rate = round((bookings_window / calls_window) * 100, 1) if calls_window else 0
        avg_revenue_per_booking = round((total_revenue / total_bookings), 2) if total_bookings else 0

        return {
            "windowDays": days,
            "totalBookings": total_bookings,
            "totalRevenue": float(total_revenue or 0),
            "bookingsInWindow": bookings_window,
            "revenueInWindow": float(revenue_window or 0),
            "callsInWindow": calls_window,
            "conversionRate": conversion_rate,
            "avgRevenuePerBooking": avg_revenue_per_booking,
            "daily": daily,
        }

