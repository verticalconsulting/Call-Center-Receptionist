"""Google Calendar booking sync and reminder orchestration."""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.services.data_store import DataStore
from app.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    if len(digits) == 10:
        return f"+1{digits}"
    if phone and phone.startswith("+"):
        return phone
    return f"+{digits}" if digits else phone


def _load_customer_routing() -> dict:
    with open(PROJECT_ROOT / "customer_routing.json", "r", encoding="utf-8") as f:
        return json.load(f)


@dataclass
class BookingConfig:
    timezone: str
    google_calendar_id: str
    google_service_account_json: str
    google_service_account_file: str
    reminder_lead_hours: int
    party_duration_minutes: int
    camp_duration_minutes: int
    camp_default_start_time: str
    default_party_revenue: float
    default_camp_revenue: float


class BookingService:
    """Creates Google Calendar events and schedules reminders."""

    def __init__(self, config: BookingConfig, reminder_service: ReminderService, data_store: DataStore):
        self.config = config
        self.reminder_service = reminder_service
        self.data_store = data_store
        self.tz = ZoneInfo(self.config.timezone)

    def is_enabled(self) -> bool:
        return bool(
            self._resolve_calendar_id("default")
            and (self.config.google_service_account_json or self.config.google_service_account_file)
        )

    def _credentials(self):
        info = None
        if self.config.google_service_account_json:
            info = json.loads(self.config.google_service_account_json)
        elif self.config.google_service_account_file:
            with open(self.config.google_service_account_file, "r", encoding="utf-8") as f:
                info = json.load(f)
        if not info:
            raise RuntimeError("Google service account credentials are not configured")
        return service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )

    def _calendar(self):
        return build("calendar", "v3", credentials=self._credentials(), cache_discovery=False)

    def _resolve_customer_config(self, customer_id: str) -> Dict[str, Any]:
        routing = _load_customer_routing()
        for _, cfg in routing.get("customers", {}).items():
            if cfg.get("customer_id") == customer_id:
                return cfg
        return routing.get("default", {})

    def _resolve_calendar_id(self, customer_id: str) -> str:
        cfg = self._resolve_customer_config(customer_id)
        return cfg.get("google_calendar_id") or self.config.google_calendar_id

    def _parse_local_datetime(self, date_str: str, time_str: str) -> datetime:
        hour, minute = (time_str or "09:00").split(":")
        return datetime(
            year=int(date_str[0:4]),
            month=int(date_str[5:7]),
            day=int(date_str[8:10]),
            hour=int(hour),
            minute=int(minute),
            tzinfo=self.tz,
        )

    def check_availability(self, customer_id: str, start_iso: str, end_iso: str) -> Dict[str, Any]:
        calendar_id = self._resolve_calendar_id(customer_id)
        if not calendar_id:
            raise RuntimeError("Google calendar ID is not configured")

        start_dt = datetime.fromisoformat(start_iso)
        end_dt = datetime.fromisoformat(end_iso)
        items = (
            self._calendar()
            .events()
            .list(
                calendarId=calendar_id,
                timeMin=start_dt.astimezone(timezone.utc).isoformat(),
                timeMax=end_dt.astimezone(timezone.utc).isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
            .get("items", [])
        )

        conflicts = [
            {
                "id": i.get("id"),
                "summary": i.get("summary"),
                "start": (i.get("start", {}).get("dateTime") or i.get("start", {}).get("date")),
                "end": (i.get("end", {}).get("dateTime") or i.get("end", {}).get("date")),
            }
            for i in items
            if i.get("status") != "cancelled"
        ]
        return {"available": len(conflicts) == 0, "conflicts": conflicts}

    def create_booking(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        booking_type = payload.get("bookingType")
        customer_id = payload.get("customerId", "default")

        if booking_type == "birthday_party":
            return self._create_party_booking(customer_id, payload)
        if booking_type == "camp_registration":
            return self._create_camp_booking(customer_id, payload)
        raise ValueError("Unsupported bookingType")

    def _create_party_booking(self, customer_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        start_local = self._parse_local_datetime(payload["preferredDate"], payload["preferredTime"])
        end_local = start_local + timedelta(minutes=self.config.party_duration_minutes)

        availability = self.check_availability(customer_id, start_local.isoformat(), end_local.isoformat())
        if not availability["available"]:
            return {
                "status": "conflict",
                "message": "Selected time is not available.",
                "availability": availability,
            }

        summary = f"Birthday Party - {payload['childName']}"
        description = (
            f"Customer: {customer_id}\n"
            f"Parent: {payload['parentName']}\n"
            f"Phone: {payload['phoneNumber']}\n"
            f"Child: {payload['childName']} ({payload['childAge']})\n"
            f"Kids attending: {payload['numberOfKids']}\n"
            f"Notes: {payload.get('additionalNotes', '')}"
        )
        event = self._insert_event(customer_id, summary, description, start_local, end_local)

        reminder_id = None
        if self._sms_opted_in(payload):
            reminder_id = self._schedule_reminder(
                booking_id=event["id"],
                to_phone=_normalize_phone(payload["phoneNumber"]),
                parent_name=payload["parentName"],
                child_name=payload["childName"],
                booking_label="birthday party",
                start_time=start_local,
            )
        estimated_revenue = float(payload.get("estimatedRevenue") or self.config.default_party_revenue)
        booking_row_id = self.data_store.insert_booking(
            customer_id=customer_id,
            booking_type="birthday_party",
            parent_name=payload["parentName"],
            phone_number=_normalize_phone(payload["phoneNumber"]),
            child_name=payload["childName"],
            start_time_utc=start_local.astimezone(timezone.utc).isoformat(),
            end_time_utc=end_local.astimezone(timezone.utc).isoformat(),
            status="confirmed",
            estimated_revenue=estimated_revenue,
            google_event_id=event.get("id"),
            google_event_link=event.get("htmlLink"),
            reminder_id=reminder_id,
            metadata={
                "childAge": payload.get("childAge"),
                "numberOfKids": payload.get("numberOfKids"),
                "preferredTime": payload.get("preferredTime"),
                "additionalNotes": payload.get("additionalNotes"),
            },
        )

        return {
            "status": "confirmed",
            "event": event,
            "reminderId": reminder_id,
            "bookingId": booking_row_id,
        }

    def _create_camp_booking(self, customer_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        created: List[Dict[str, Any]] = []
        conflicts: List[Dict[str, Any]] = []

        for camp_date in payload.get("campDates", []):
            start_local = self._parse_local_datetime(camp_date, self.config.camp_default_start_time)
            end_local = start_local + timedelta(minutes=self.config.camp_duration_minutes)
            availability = self.check_availability(customer_id, start_local.isoformat(), end_local.isoformat())
            if not availability["available"]:
                conflicts.append({"date": camp_date, "availability": availability})
                continue

            summary = f"Camp Registration - {payload['childName']} ({payload['sport']})"
            description = (
                f"Customer: {customer_id}\n"
                f"Parent: {payload['parentName']}\n"
                f"Phone: {payload['phoneNumber']}\n"
                f"Child: {payload['childName']} ({payload['childAge']})\n"
                f"Sport: {payload['sport']}\n"
                f"Level: {payload['experienceLevel']}\n"
                f"Notes: {payload.get('additionalNotes', '')}"
            )
            event = self._insert_event(customer_id, summary, description, start_local, end_local)
            reminder_id = None
            if self._sms_opted_in(payload):
                reminder_id = self._schedule_reminder(
                    booking_id=event["id"],
                    to_phone=_normalize_phone(payload["phoneNumber"]),
                    parent_name=payload["parentName"],
                    child_name=payload["childName"],
                    booking_label="camp",
                    start_time=start_local,
                )
            estimated_revenue = float(payload.get("estimatedRevenue") or self.config.default_camp_revenue)
            booking_row_id = self.data_store.insert_booking(
                customer_id=customer_id,
                booking_type="camp_registration",
                parent_name=payload["parentName"],
                phone_number=_normalize_phone(payload["phoneNumber"]),
                child_name=payload["childName"],
                start_time_utc=start_local.astimezone(timezone.utc).isoformat(),
                end_time_utc=end_local.astimezone(timezone.utc).isoformat(),
                status="confirmed",
                estimated_revenue=estimated_revenue,
                google_event_id=event.get("id"),
                google_event_link=event.get("htmlLink"),
                reminder_id=reminder_id,
                metadata={
                    "childAge": payload.get("childAge"),
                    "sport": payload.get("sport"),
                    "experienceLevel": payload.get("experienceLevel"),
                    "additionalNotes": payload.get("additionalNotes"),
                },
            )
            created.append({"event": event, "reminderId": reminder_id, "bookingId": booking_row_id})

        if created and not conflicts:
            return {"status": "confirmed", "bookings": created}
        if created and conflicts:
            return {"status": "partial", "bookings": created, "conflicts": conflicts}
        return {"status": "conflict", "message": "No selected camp dates were available.", "conflicts": conflicts}

    def _insert_event(
        self,
        customer_id: str,
        summary: str,
        description: str,
        start_local: datetime,
        end_local: datetime,
    ) -> Dict[str, Any]:
        calendar_id = self._resolve_calendar_id(customer_id)
        if not calendar_id:
            raise RuntimeError("Google calendar ID is not configured")

        event_body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_local.isoformat(), "timeZone": self.config.timezone},
            "end": {"dateTime": end_local.isoformat(), "timeZone": self.config.timezone},
        }
        event = (
            self._calendar()
            .events()
            .insert(calendarId=calendar_id, body=event_body)
            .execute()
        )
        return {
            "id": event.get("id"),
            "htmlLink": event.get("htmlLink"),
            "start": event.get("start", {}).get("dateTime"),
            "end": event.get("end", {}).get("dateTime"),
            "summary": event.get("summary"),
        }

    def _schedule_reminder(
        self,
        booking_id: str,
        to_phone: str,
        parent_name: str,
        child_name: str,
        booking_label: str,
        start_time: datetime,
    ) -> str:
        reminder_time = start_time.astimezone(timezone.utc) - timedelta(hours=self.config.reminder_lead_hours)
        if reminder_time <= datetime.now(timezone.utc):
            reminder_time = datetime.now(timezone.utc) + timedelta(minutes=1)

        message = (
            f"Hi {parent_name}, reminder for {child_name}'s {booking_label} at D-BAT Pearl on "
            f"{start_time.strftime('%A, %B %d at %I:%M %p')}."
        )
        return self.reminder_service.queue_reminder(
            booking_id=booking_id or str(uuid.uuid4()),
            to_phone=to_phone,
            message=message,
            send_at_utc=reminder_time,
        )

    def _sms_opted_in(self, payload: Dict[str, Any]) -> bool:
        # Preserve existing behavior for callers that do not send an opt-in flag (e.g., AI call flow).
        if "smsOptIn" not in payload:
            return True
        return bool(payload.get("smsOptIn"))
