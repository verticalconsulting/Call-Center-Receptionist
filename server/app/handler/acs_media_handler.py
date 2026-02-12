"""Handles media streaming to Azure Voice Live API via WebSocket."""

import asyncio
import base64
from datetime import datetime, timedelta, timezone
import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from azure.identity.aio import ManagedIdentityCredential
from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import BlobServiceClient
from app.services.data_store import DataStore
from websockets.asyncio.client import connect as ws_connect
from websockets.typing import Data

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Event type constants
SESSION_CREATED = "session.created"
INPUT_AUDIO_BUFFER_CLEARED = "input_audio_buffer.cleared"
INPUT_AUDIO_BUFFER_SPEECH_STARTED = "input_audio_buffer.speech_started"
INPUT_AUDIO_BUFFER_SPEECH_STOPPED = "input_audio_buffer.speech_stopped"
CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED = "conversation.item.input_audio_transcription.completed"
CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_FAILED = "conversation.item.input_audio_transcription.failed"
RESPONSE_DONE = "response.done"
RESPONSE_AUDIO_TRANSCRIPT_DONE = "response.audio_transcript.done"
RESPONSE_AUDIO_DELTA = "response.audio.delta"
ERROR = "error"


def load_system_prompt(prompt_file: str = "grace_intake_agent.txt") -> str:
    """
    Load system prompt from external configuration file.

    Args:
        prompt_file: Name of the prompt file in server/prompts/ directory

    Returns:
        System prompt text

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    # server/app/handler/acs_media_handler.py -> server/
    prompts_dir = PROJECT_ROOT / "prompts"
    prompt_path = prompts_dir / prompt_file

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            instructions = f.read().strip()
            logger.info("[ACSMediaHandler] Loaded system prompt from %s (%d chars)",
                       prompt_path, len(instructions))
            return instructions
    except FileNotFoundError:
        logger.error("[ACSMediaHandler] Prompt file not found: %s", prompt_path)
        # Fallback to basic prompt
        fallback = (
            "You are Grace, a friendly and knowledgeable intake agent for Mercy House and Sacred Grove. "
            "Help callers with questions about the programs and collect their contact information."
        )
        logger.warning("[ACSMediaHandler] Using fallback prompt (%d chars)", len(fallback))
        return fallback
    except Exception as e:
        logger.exception("[ACSMediaHandler] Error loading prompt file: %s", e)
        raise


def load_customer_routing() -> dict:
    """
    Load customer routing configuration from JSON file.

    Returns:
        Dictionary with customer routing config
    """
    routing_path = PROJECT_ROOT / "customer_routing.json"

    try:
        with open(routing_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            logger.info("[ACSMediaHandler] Loaded customer routing config with %d customers",
                       len(config.get("customers", {})))
            return config
    except FileNotFoundError:
        logger.warning("[ACSMediaHandler] customer_routing.json not found, using default routing")
        return {"customers": {}, "default": {"customer_id": "default", "prompt_file": "grace_intake_agent.txt"}}
    except Exception as e:
        logger.exception("[ACSMediaHandler] Error loading customer routing: %s", e)
        return {"customers": {}, "default": {"customer_id": "default", "prompt_file": "grace_intake_agent.txt"}}


def get_customer_config_by_id(customer_id: str) -> dict:
    """
    Get customer configuration by customer ID.

    Args:
        customer_id: The customer identifier

    Returns:
        Customer configuration with prompt_file, voice settings, etc.
    """
    routing_config = load_customer_routing()

    # Search through customers for matching ID
    for phone, config in routing_config.get("customers", {}).items():
        if config.get("customer_id") == customer_id:
            logger.info("[ACSMediaHandler] Found config for customer: %s", customer_id)
            return config

    # Fall back to default
    default_config = routing_config.get("default", {
        "customer_id": "default",
        "prompt_file": "grace_intake_agent.txt",
        "voice_name": "en-US-Emma2:DragonHDLatestNeural",
        "voice_temperature": 0.8
    })
    logger.info("[ACSMediaHandler] Using default config for customer: %s", customer_id)
    return default_config


def session_config(customer_id: str = "default"):
    """
    Returns session configuration for Voice Live based on customer.

    Args:
        customer_id: The customer identifier for routing-specific configuration
    """
    customer_config = get_customer_config_by_id(customer_id)

    prompt_file = customer_config.get("prompt_file", "grace_intake_agent.txt")
    voice_name = customer_config.get("voice_name", "en-US-Emma2:DragonHDLatestNeural")
    voice_temp = customer_config.get("voice_temperature", 0.8)

    logger.info("[ACSMediaHandler] Session config: customer=%s, prompt=%s, voice=%s",
               customer_id, prompt_file, voice_name)

    return {
        "type": "session.update",
        "session": {
            "instructions": load_system_prompt(prompt_file),
            "turn_detection": {
                "type": "azure_semantic_vad",
                "threshold": 0.25,
                "prefix_padding_ms": 200,
                "silence_duration_ms": 250,
                "remove_filler_words": False,
            },
            "input_audio_transcription": {
                "model": "whisper-1"
            },
            "input_audio_noise_reduction": {"type": "azure_deep_noise_suppression"},
            "input_audio_echo_cancellation": {"type": "server_echo_cancellation"},
            "voice": {
                "name": voice_name,
                "type": "azure-standard",
                "temperature": voice_temp
            },
        },
    }

class ACSMediaHandler:
    """Manages audio streaming between client and Azure Voice Live API."""

    def __init__(self, config: Dict[str, Any], customer_id: str = "default"):
        self.endpoint: str = config["AZURE_VOICE_LIVE_ENDPOINT"]
        self.model: str = config["VOICE_LIVE_MODEL"]
        self.api_key: Optional[str] = config["AZURE_VOICE_LIVE_API_KEY"]
        self.client_id: Optional[str] = config["AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID"]
        self.storage_account_url: Optional[str] = config.get("AZURE_STORAGE_ACCOUNT_URL")
        self.storage_container: str = config.get("AZURE_STORAGE_CONTAINER", "conversation-logs")
        self.data_store: Optional[DataStore] = config.get("DATA_STORE")
        self.booking_service = config.get("BOOKING_SERVICE")
        self.booking_timezone = config.get("BOOKING_TIMEZONE", "America/Chicago")
        self.customer_id: str = customer_id
        self.send_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.ws: Optional[Any] = None
        self.send_task: Optional[asyncio.Task] = None
        self.receiver_task: Optional[asyncio.Task] = None
        self.incoming_websocket: Optional[Any] = None
        self.is_raw_audio: bool = True

        # Conversation tracking
        self.session_id: str = self._generate_guid()
        self.conversation_log: list = []
        self.session_start_time: datetime = datetime.now(timezone.utc)
        self.last_event_time: Optional[datetime] = None

        # Audio buffering to prevent crackling
        self.current_response_id: Optional[str] = None
        self.is_first_audio_chunk: bool = True

        logger.info("[ACSMediaHandler] Initialized for customer: %s", customer_id)

    def _generate_guid(self) -> str:
        return str(uuid.uuid4())

    def _log_conversation_event(self, event_type: str, speaker: str, text: str, metadata: Optional[Dict] = None) -> None:
        """
        Log a conversation event with timing information.

        Args:
            event_type: Type of event (transcript, speech_started, speech_stopped, etc.)
            speaker: Who is speaking (user, assistant, system)
            text: The transcript text or event description
            metadata: Additional event metadata
        """
        now = datetime.now(timezone.utc)

        # Calculate time since last event (pause/delay)
        time_since_last = None
        if self.last_event_time:
            time_since_last = (now - self.last_event_time).total_seconds()

        # Calculate time since session start
        elapsed = (now - self.session_start_time).total_seconds()

        event = {
            "timestamp": now.isoformat(),
            "elapsed_seconds": round(elapsed, 3),
            "time_since_last_event": round(time_since_last, 3) if time_since_last else None,
            "event_type": event_type,
            "speaker": speaker,
            "text": text,
            "metadata": metadata or {}
        }

        self.conversation_log.append(event)
        self.last_event_time = now

        logger.debug("[ConversationLog] %s | %s: %s", event_type, speaker, text[:100])

    async def connect(self) -> None:
        """Connects to Azure Voice Live API via WebSocket."""
        try:
            endpoint = self.endpoint.rstrip("/")
            model = self.model.strip()
            url = f"{endpoint}/voice-live/realtime?api-version=2025-05-01-preview&model={model}"
            url = url.replace("https://", "wss://")

            headers = {"x-ms-client-request-id": self._generate_guid()}

            if self.client_id:
                # Use async context manager to auto-close the credential
                async with ManagedIdentityCredential(client_id=self.client_id) as credential:
                    token = await credential.get_token(
                        "https://cognitiveservices.azure.com/.default"
                    )
                    headers["Authorization"] = f"Bearer {token.token}"
                    logger.info("[ACSMediaHandler] Connected to Voice Live API by managed identity")
            else:
                headers["api-key"] = self.api_key
                logger.info("[ACSMediaHandler] Connected to Voice Live API by API key")

            self.ws = await ws_connect(url, additional_headers=headers)
            logger.info("[ACSMediaHandler] WebSocket connection established")

            await self._send_json(session_config(self.customer_id))
            await self._send_json({"type": "response.create"})

            self.receiver_task = asyncio.create_task(self._receiver_loop())
            self.send_task = asyncio.create_task(self._sender_loop())
        except Exception as e:
            logger.exception("[ACSMediaHandler] Failed to connect to Voice Live API: %s", e)
            raise

    async def init_incoming_websocket(self, socket: Any, is_raw_audio: bool = True) -> None:
        """Sets up incoming ACS WebSocket."""
        self.incoming_websocket = socket
        self.is_raw_audio = is_raw_audio

    async def audio_to_voicelive(self, audio_b64: str) -> None:
        """Queues audio data to be sent to Voice Live API."""
        await self.send_queue.put(
            json.dumps({"type": "input_audio_buffer.append", "audio": audio_b64})
        )

    async def _send_json(self, obj: Dict[str, Any]) -> None:
        """Sends a JSON object over WebSocket."""
        if self.ws:
            await self.ws.send(json.dumps(obj))

    async def _sender_loop(self) -> None:
        """Continuously sends messages from the queue to the Voice Live WebSocket."""
        try:
            while True:
                msg = await self.send_queue.get()
                if self.ws:
                    await self.ws.send(msg)
        except asyncio.CancelledError:
            logger.info("[ACSMediaHandler] Sender loop cancelled")
            raise
        except Exception:
            logger.exception("[ACSMediaHandler] Sender loop error")

    async def _receiver_loop(self) -> None:
        """Handles incoming events from the Voice Live WebSocket."""
        try:
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type")

                match event_type:
                    case _ if event_type == SESSION_CREATED:
                        session_id = event.get("session", {}).get("id")
                        logger.info("[ACSMediaHandler] Session ID: %s", session_id)

                    case _ if event_type == INPUT_AUDIO_BUFFER_CLEARED:
                        logger.info("[ACSMediaHandler] Input audio buffer cleared")

                    case _ if event_type == INPUT_AUDIO_BUFFER_SPEECH_STARTED:
                        audio_start_ms = event.get("audio_start_ms")
                        logger.info(
                            "[ACSMediaHandler] Voice activity detection started at %s ms",
                            audio_start_ms,
                        )
                        self._log_conversation_event(
                            "speech_started",
                            "user",
                            "User started speaking",
                            {"audio_start_ms": audio_start_ms}
                        )
                        await self.stop_audio()

                    case _ if event_type == INPUT_AUDIO_BUFFER_SPEECH_STOPPED:
                        logger.info("[ACSMediaHandler] Speech stopped")
                        self._log_conversation_event(
                            "speech_stopped",
                            "user",
                            "User stopped speaking",
                            {}
                        )

                    case _ if event_type == CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED:
                        transcript = event.get("transcript")
                        logger.info("[ACSMediaHandler] User: %s", transcript)
                        self._log_conversation_event(
                            "transcript",
                            "user",
                            transcript,
                            {"item_id": event.get("item_id")}
                        )

                    case _ if event_type == CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_FAILED:
                        error_msg = event.get("error")
                        logger.warning("[ACSMediaHandler] Transcription error: %s", error_msg)

                    case _ if event_type == RESPONSE_DONE:
                        response = event.get("response", {})
                        logger.info("[ACSMediaHandler] Response done: Id=%s", response.get("id"))
                        if response.get("status_details"):
                            logger.info(
                                "[ACSMediaHandler] Status details: %s",
                                json.dumps(response["status_details"], indent=2),
                            )

                    case _ if event_type == RESPONSE_AUDIO_TRANSCRIPT_DONE:
                        transcript = event.get("transcript")
                        logger.info("[ACSMediaHandler] AI: %s", transcript)
                        self._log_conversation_event(
                            "transcript",
                            "assistant",
                            transcript,
                            {"response_id": event.get("response_id"), "item_id": event.get("item_id")}
                        )
                        await self.send_message(
                            json.dumps({"Kind": "Transcription", "Text": transcript})
                        )

                    case _ if event_type == RESPONSE_AUDIO_DELTA:
                        delta = event.get("delta")
                        response_id = event.get("response_id")

                        # Track response changes to detect first audio chunk
                        if response_id != self.current_response_id:
                            self.current_response_id = response_id
                            self.is_first_audio_chunk = True

                        if self.is_raw_audio:
                            audio_bytes = base64.b64decode(delta)

                            # Add silence padding to first chunk to prevent crackling
                            if self.is_first_audio_chunk:
                                # 50ms of silence at 24kHz, 16-bit, mono = 2400 samples = 4800 bytes
                                silence_padding = b'\x00' * 2400
                                audio_bytes = silence_padding + audio_bytes
                                self.is_first_audio_chunk = False
                                logger.debug("[ACSMediaHandler] Added silence padding to first audio chunk")

                            await self.send_message(audio_bytes)
                        else:
                            await self.voicelive_to_acs(delta, self.is_first_audio_chunk)
                            if self.is_first_audio_chunk:
                                self.is_first_audio_chunk = False

                    case _ if event_type == ERROR:
                        logger.error("[ACSMediaHandler] Voice Live error: %s", event)

                    case _:
                        logger.debug("[ACSMediaHandler] Other event: %s", event_type)
        except asyncio.CancelledError:
            logger.info("[ACSMediaHandler] Receiver loop cancelled")
            raise
        except Exception:
            logger.exception("[ACSMediaHandler] Receiver loop error")

    async def send_message(self, message: Data) -> None:
        """Sends data back to client WebSocket."""
        try:
            await self.incoming_websocket.send(message)
        except Exception:
            logger.exception("[ACSMediaHandler] Failed to send message")

    async def voicelive_to_acs(self, base64_data: str, add_padding: bool = False) -> None:
        """Converts Voice Live audio delta to ACS audio message."""
        try:
            # Add silence padding to first chunk if requested
            if add_padding:
                audio_bytes = base64.b64decode(base64_data)
                # 50ms of silence at 24kHz, 16-bit, mono = 2400 samples = 4800 bytes
                silence_padding = b'\x00' * 2400
                audio_bytes = silence_padding + audio_bytes
                base64_data = base64.b64encode(audio_bytes).decode('utf-8')
                logger.debug("[ACSMediaHandler] Added silence padding to first ACS audio chunk")

            data = {
                "Kind": "AudioData",
                "AudioData": {"Data": base64_data},
                "StopAudio": None,
            }
            await self.send_message(json.dumps(data))
        except Exception:
            logger.exception("[ACSMediaHandler] Error in voicelive_to_acs")

    async def stop_audio(self) -> None:
        """Sends a StopAudio signal to ACS."""
        stop_audio_data = {"Kind": "StopAudio", "AudioData": None, "StopAudio": {}}
        await self.send_message(json.dumps(stop_audio_data))

    async def acs_to_voicelive(self, stream_data: str) -> None:
        """Processes audio from ACS and forwards to Voice Live if not silent."""
        try:
            data = json.loads(stream_data)
            if data.get("kind") == "AudioData":
                audio_data = data.get("audioData", {})
                if not audio_data.get("silent", True):
                    await self.audio_to_voicelive(audio_data.get("data"))
        except Exception:
            logger.exception("[ACSMediaHandler] Error processing ACS audio")

    async def web_to_voicelive(self, audio_bytes: bytes) -> None:
        """Encodes raw audio bytes and sends to Voice Live API."""
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
        await self.audio_to_voicelive(audio_b64)

    async def save_conversation_log(self) -> Optional[Path]:
        """
        Save conversation log to local file and/or Azure Blob Storage.

        Returns:
            Path to the saved log file, or None if no conversation to save
        """
        if not self.conversation_log:
            logger.warning("[ACSMediaHandler] No conversation data to save")
            return None

        # Generate filename with timestamp
        timestamp = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}_{self.session_id[:8]}.json"

        # Calculate session duration
        duration = (datetime.now(timezone.utc) - self.session_start_time).total_seconds()

        # Prepare conversation summary
        conversation_data = {
            "session_id": self.session_id,
            "session_start": self.session_start_time.isoformat(),
            "session_duration_seconds": round(duration, 2),
            "total_events": len(self.conversation_log),
            "model": self.model,
            "endpoint": self.endpoint,
            "conversation": self.conversation_log
        }

        conversation_json = json.dumps(conversation_data, indent=2, ensure_ascii=False)

        # Persist structured call data for reporting/API usage.
        try:
            if self.data_store:
                user_turns = [e for e in self.conversation_log if e.get("event_type") == "transcript" and e.get("speaker") == "user"]
                assistant_turns = [e for e in self.conversation_log if e.get("event_type") == "transcript" and e.get("speaker") == "assistant"]
                self.data_store.insert_call_log(
                    session_id=self.session_id,
                    customer_id=self.customer_id,
                    channel="web" if self.is_raw_audio else "acs",
                    started_at_utc=self.session_start_time.astimezone(timezone.utc).isoformat(),
                    ended_at_utc=datetime.now(timezone.utc).isoformat(),
                    duration_seconds=round(duration, 2),
                    user_turns=len(user_turns),
                    assistant_turns=len(assistant_turns),
                    first_user_utterance=(user_turns[0].get("text") if user_turns else None),
                    first_assistant_utterance=(assistant_turns[0].get("text") if assistant_turns else None),
                    transcript=self.conversation_log,
                )
        except Exception as e:
            logger.exception("[ACSMediaHandler] Error saving call data to database: %s", e)

        # Attempt booking capture from completed call transcript.
        try:
            await self._auto_capture_booking_from_transcript()
        except Exception as e:
            logger.exception("[ACSMediaHandler] Error during call booking automation: %s", e)

        # Save to Azure Blob Storage if configured
        if self.storage_account_url and self.client_id:
            try:
                async with ManagedIdentityCredential(client_id=self.client_id) as credential:
                    async with BlobServiceClient(
                        account_url=self.storage_account_url,
                        credential=credential
                    ) as blob_service_client:
                        container_client = blob_service_client.get_container_client(self.storage_container)

                        # Create container if it doesn't exist
                        try:
                            await container_client.create_container()
                            logger.info("[ACSMediaHandler] Created container: %s", self.storage_container)
                        except Exception:
                            pass  # Container already exists

                        # Upload blob
                        blob_client = container_client.get_blob_client(filename)
                        await blob_client.upload_blob(
                            conversation_json.encode('utf-8'),
                            overwrite=True,
                            content_settings=ContentSettings(content_type='application/json')
                        )
                        logger.info("[ACSMediaHandler] Conversation log saved to blob storage: %s/%s",
                                   self.storage_container, filename)
            except Exception as e:
                logger.exception("[ACSMediaHandler] Error saving to blob storage: %s", e)

        # Also save locally for development/debugging
        try:
            logs_dir = Path("/tmp/conversation_logs")
            logs_dir.mkdir(exist_ok=True)
            log_path = logs_dir / filename

            with open(log_path, "w", encoding="utf-8") as f:
                f.write(conversation_json)

            logger.info("[ACSMediaHandler] Conversation log saved locally: %s", log_path)
            return log_path

        except Exception as e:
            logger.exception("[ACSMediaHandler] Error saving local conversation log: %s", e)
            return None

    def _extract_phone(self, text: str) -> Optional[str]:
        digits = re.sub(r"\D", "", text or "")
        if len(digits) >= 10:
            digits = digits[-10:]
            return f"+1{digits}"
        return None

    def _extract_booking_candidate(self) -> Optional[Dict[str, Any]]:
        transcript_events = [e for e in self.conversation_log if e.get("event_type") == "transcript"]
        if not transcript_events:
            return None

        user_texts = [e.get("text", "") for e in transcript_events if e.get("speaker") == "user"]
        all_texts = [e.get("text", "") for e in transcript_events]
        user_joined = " ".join(user_texts)
        all_joined = " ".join(all_texts)
        lowered = all_joined.lower()

        booking_type = None
        if "birthday party" in lowered or "party" in lowered:
            booking_type = "birthday_party"
        elif "camp" in lowered:
            booking_type = "camp_registration"
        if not booking_type:
            return None

        parent_name = "Unknown Caller"
        m_parent = re.search(r"\bthis is ([A-Za-z]+(?: [A-Za-z]+)?)", all_joined, flags=re.IGNORECASE)
        if m_parent:
            parent_name = m_parent.group(1).strip().title()

        child_name = "Unknown Child"
        m_child = re.search(r"\bfor ([A-Za-z]+(?: [A-Za-z]+)?)", all_joined, flags=re.IGNORECASE)
        if m_child:
            child_name = m_child.group(1).strip().title()

        phone = self._extract_phone(all_joined) or "+10000000000"

        age = "0"
        m_age = re.search(r"\b(?:he'?s|she'?s|is|turning)\s*(\d{1,2})\b", all_joined, flags=re.IGNORECASE)
        if m_age:
            age = m_age.group(1)

        kids = "1"
        m_kids = re.search(r"\b(\d{1,3})\s*(?:kids|children)\b", all_joined, flags=re.IGNORECASE)
        if m_kids:
            kids = m_kids.group(1)

        local_start = self._extract_local_start_datetime(all_joined, booking_type)
        if not local_start:
            return None

        return {
            "bookingType": booking_type,
            "customerId": self.customer_id,
            "parentName": parent_name,
            "phoneNumber": phone,
            "childName": child_name,
            "childAge": age,
            "numberOfKids": kids,
            "preferredDate": local_start.strftime("%Y-%m-%d"),
            "preferredTime": local_start.strftime("%H:%M"),
            "campDates": [local_start.strftime("%Y-%m-%d")],
            "sport": "baseball",
            "experienceLevel": "intermediate",
            "additionalNotes": "Auto-captured from voice call transcript.",
        }

    def _extract_local_start_datetime(self, text: str, booking_type: str) -> Optional[datetime]:
        tz = ZoneInfo(self.booking_timezone)
        now_local = datetime.now(tz)
        lowered = text.lower()

        weekday_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
        }
        target_date = None
        for name, idx in weekday_map.items():
            if f"next {name}" in lowered or re.search(rf"\b{name}\b", lowered):
                delta = (idx - now_local.weekday()) % 7
                if delta == 0:
                    delta = 7
                target_date = (now_local + timedelta(days=delta)).date()
                break

        if not target_date:
            m_date = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", lowered)
            if m_date:
                target_date = datetime.fromisoformat(m_date.group(1)).date()
        if not target_date:
            return None

        hour, minute = (15, 0) if booking_type == "birthday_party" else (9, 0)
        m_time = re.search(r"\bat\s*(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?\b", lowered)
        if m_time:
            hour = int(m_time.group(1))
            minute = int(m_time.group(2) or 0)
            ampm = m_time.group(3)
            if ampm:
                ampm = ampm.replace(".", "")
                if ampm.startswith("p") and hour < 12:
                    hour += 12
                if ampm.startswith("a") and hour == 12:
                    hour = 0

        return datetime(
            year=target_date.year,
            month=target_date.month,
            day=target_date.day,
            hour=hour,
            minute=minute,
            tzinfo=tz,
        )

    async def _auto_capture_booking_from_transcript(self) -> None:
        # Only auto-capture bookings from phone/ACS calls.
        if self.is_raw_audio:
            return

        candidate = self._extract_booking_candidate()
        if not candidate:
            return

        # Try full booking flow (calendar + reminders + DB) when integration is configured.
        if self.booking_service and self.booking_service.is_enabled():
            result = self.booking_service.create_booking(candidate)
            logger.info("[ACSMediaHandler] Auto booking result: %s", result.get("status"))
            return

        # Fallback: ensure booking still appears in admin/data even without calendar integration.
        if self.data_store:
            local_start = datetime.strptime(
                f"{candidate['preferredDate']} {candidate['preferredTime']}",
                "%Y-%m-%d %H:%M",
            ).replace(tzinfo=ZoneInfo(self.booking_timezone))
            duration_minutes = 120 if candidate["bookingType"] == "birthday_party" else 180
            local_end = local_start + timedelta(minutes=duration_minutes)
            self.data_store.insert_booking(
                customer_id=candidate["customerId"],
                booking_type=candidate["bookingType"],
                parent_name=candidate["parentName"],
                phone_number=candidate["phoneNumber"],
                child_name=candidate["childName"],
                start_time_utc=local_start.astimezone(timezone.utc).isoformat(),
                end_time_utc=local_end.astimezone(timezone.utc).isoformat(),
                status="captured_from_call",
                estimated_revenue=0,
                metadata={
                    "source": "voice_call_auto_capture",
                    "session_id": self.session_id,
                },
            )
            logger.info("[ACSMediaHandler] Stored fallback booking from call transcript")

    async def close(self) -> None:
        """Closes WebSocket connection and cancels background tasks."""
        logger.info("[ACSMediaHandler] Closing handler")

        # Save conversation log before closing
        await self.save_conversation_log()

        # Cancel background tasks
        if self.send_task and not self.send_task.done():
            self.send_task.cancel()
            try:
                await self.send_task
            except asyncio.CancelledError:
                pass

        if self.receiver_task and not self.receiver_task.done():
            self.receiver_task.cancel()
            try:
                await self.receiver_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket connection
        if self.ws:
            await self.ws.close()
            self.ws = None

        logger.info("[ACSMediaHandler] Handler closed successfully")
