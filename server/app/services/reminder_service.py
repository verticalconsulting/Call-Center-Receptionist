"""Schedules and sends SMS reminders for bookings."""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from azure.communication.sms import SmsClient

logger = logging.getLogger(__name__)


@dataclass
class ReminderConfig:
    db_path: str
    sms_connection_string: str
    sms_from_number: str


class ReminderService:
    """Persistent reminder queue with in-process scheduler."""

    def __init__(self, config: ReminderConfig):
        self.config = config
        self.scheduler = AsyncIOScheduler(timezone=timezone.utc)
        self.started = False
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.config.db_path, check_same_thread=False)

    def _init_db(self) -> None:
        db_dir = Path(self.config.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    reminder_id TEXT PRIMARY KEY,
                    booking_id TEXT NOT NULL,
                    to_phone TEXT NOT NULL,
                    message TEXT NOT NULL,
                    send_at_utc TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at_utc TEXT NOT NULL,
                    sent_at_utc TEXT,
                    error TEXT
                )
                """
            )
            conn.commit()

    def start(self) -> None:
        if self.started:
            return
        self.scheduler.start()
        self.started = True
        self._schedule_pending()

    async def shutdown(self) -> None:
        if not self.started:
            return
        self.scheduler.shutdown(wait=False)
        self.started = False

    def queue_reminder(
        self,
        booking_id: str,
        to_phone: str,
        message: str,
        send_at_utc: datetime,
    ) -> str:
        reminder_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO reminders
                (reminder_id, booking_id, to_phone, message, send_at_utc, created_at_utc)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    reminder_id,
                    booking_id,
                    to_phone,
                    message,
                    send_at_utc.astimezone(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        self._schedule_job(reminder_id, send_at_utc)
        return reminder_id

    def _schedule_pending(self) -> None:
        now = datetime.now(timezone.utc)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT reminder_id, send_at_utc
                FROM reminders
                WHERE status = 'pending'
                """
            ).fetchall()
        for reminder_id, send_at_utc in rows:
            send_at = datetime.fromisoformat(send_at_utc)
            if send_at < now:
                send_at = now
            self._schedule_job(reminder_id, send_at)

    def _schedule_job(self, reminder_id: str, send_at_utc: datetime) -> None:
        if not self.started:
            return
        self.scheduler.add_job(
            self._dispatch_reminder,
            trigger=DateTrigger(run_date=send_at_utc.astimezone(timezone.utc)),
            args=[reminder_id],
            id=reminder_id,
            replace_existing=True,
            misfire_grace_time=3600,
        )

    async def _dispatch_reminder(self, reminder_id: str) -> None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT to_phone, message, status
                FROM reminders
                WHERE reminder_id = ?
                """,
                (reminder_id,),
            ).fetchone()
        if not row:
            return

        to_phone, message, status = row
        if status != "pending":
            return

        try:
            if not self.config.sms_connection_string or not self.config.sms_from_number:
                raise RuntimeError("ACS SMS configuration is missing")

            await asyncio.to_thread(self._send_sms, to_phone, message)

            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE reminders
                    SET status = 'sent', sent_at_utc = ?, error = NULL
                    WHERE reminder_id = ?
                    """,
                    (datetime.now(timezone.utc).isoformat(), reminder_id),
                )
                conn.commit()
            logger.info("[ReminderService] Reminder sent: %s", reminder_id)
        except Exception as exc:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE reminders
                    SET status = 'failed', error = ?
                    WHERE reminder_id = ?
                    """,
                    (str(exc), reminder_id),
                )
                conn.commit()
            logger.exception("[ReminderService] Failed sending reminder %s", reminder_id)

    def _send_sms(self, to_phone: str, message: str) -> None:
        client = SmsClient.from_connection_string(self.config.sms_connection_string)
        results = client.send(
            from_=self.config.sms_from_number,
            to=[to_phone],
            message=message,
            enable_delivery_report=True,
        )
        if not results or not getattr(results[0], "successful", False):
            details = results[0] if results else "no result"
            raise RuntimeError(f"SMS send failed: {details}")

