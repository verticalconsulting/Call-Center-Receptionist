import asyncio
import logging
import os
from pathlib import Path

from app.handler.acs_event_handler import AcsEventHandler
from app.handler.acs_media_handler import ACSMediaHandler
from app.services.booking_service import BookingConfig, BookingService
from app.services.data_store import DataStore
from app.services.reminder_service import ReminderConfig, ReminderService
try:
    from dotenv import load_dotenv  # optional dependency; fall back if not installed
except Exception:
    def load_dotenv():
        # no-op if python-dotenv is not available
        return False
from quart import Quart, jsonify, redirect, request, send_from_directory, websocket

load_dotenv()

app = Quart(__name__)
app.config["AZURE_VOICE_LIVE_API_KEY"] = os.getenv("AZURE_VOICE_LIVE_API_KEY", "")
app.config["AZURE_VOICE_LIVE_ENDPOINT"] = os.getenv("AZURE_VOICE_LIVE_ENDPOINT")
app.config["VOICE_LIVE_MODEL"] = os.getenv("VOICE_LIVE_MODEL", "gpt-realtime")
app.config["ACS_CONNECTION_STRING"] = os.getenv("ACS_CONNECTION_STRING")
app.config["ACS_DEV_TUNNEL"] = os.getenv("ACS_DEV_TUNNEL", "")
app.config["AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID"] = os.getenv(
    "AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID", ""
)
app.config["AZURE_STORAGE_ACCOUNT_URL"] = os.getenv("AZURE_STORAGE_ACCOUNT_URL", "")
app.config["AZURE_STORAGE_CONTAINER"] = os.getenv("AZURE_STORAGE_CONTAINER", "conversation-logs")
app.config["GOOGLE_SERVICE_ACCOUNT_JSON"] = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
app.config["GOOGLE_SERVICE_ACCOUNT_FILE"] = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
app.config["GOOGLE_CALENDAR_ID"] = os.getenv("GOOGLE_CALENDAR_ID", "")
app.config["BOOKING_TIMEZONE"] = os.getenv("BOOKING_TIMEZONE", "America/Chicago")
app.config["ACS_SMS_FROM"] = os.getenv("ACS_SMS_FROM", "")
app.config["BOOKING_REMINDER_LEAD_HOURS"] = int(os.getenv("BOOKING_REMINDER_LEAD_HOURS", "48"))
app.config["BOOKING_DB_PATH"] = os.getenv("BOOKING_DB_PATH", "/tmp/bookings.db")
app.config["BOOKING_PARTY_DURATION_MINUTES"] = int(os.getenv("BOOKING_PARTY_DURATION_MINUTES", "120"))
app.config["BOOKING_CAMP_DURATION_MINUTES"] = int(os.getenv("BOOKING_CAMP_DURATION_MINUTES", "180"))
app.config["BOOKING_CAMP_DEFAULT_START_TIME"] = os.getenv("BOOKING_CAMP_DEFAULT_START_TIME", "09:00")
app.config["BOOKING_DEFAULT_PARTY_REVENUE"] = float(os.getenv("BOOKING_DEFAULT_PARTY_REVENUE", "350"))
app.config["BOOKING_DEFAULT_CAMP_REVENUE"] = float(os.getenv("BOOKING_DEFAULT_CAMP_REVENUE", "125"))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s"
)

acs_handler = AcsEventHandler(app.config)
data_store = DataStore(app.config["BOOKING_DB_PATH"])
app.config["DATA_STORE"] = data_store
reminder_service = ReminderService(
    ReminderConfig(
        db_path=app.config["BOOKING_DB_PATH"],
        sms_connection_string=app.config["ACS_CONNECTION_STRING"],
        sms_from_number=app.config["ACS_SMS_FROM"],
    )
)
booking_service = BookingService(
    BookingConfig(
        timezone=app.config["BOOKING_TIMEZONE"],
        google_calendar_id=app.config["GOOGLE_CALENDAR_ID"],
        google_service_account_json=app.config["GOOGLE_SERVICE_ACCOUNT_JSON"],
        google_service_account_file=app.config["GOOGLE_SERVICE_ACCOUNT_FILE"],
        reminder_lead_hours=app.config["BOOKING_REMINDER_LEAD_HOURS"],
        party_duration_minutes=app.config["BOOKING_PARTY_DURATION_MINUTES"],
        camp_duration_minutes=app.config["BOOKING_CAMP_DURATION_MINUTES"],
        camp_default_start_time=app.config["BOOKING_CAMP_DEFAULT_START_TIME"],
        default_party_revenue=app.config["BOOKING_DEFAULT_PARTY_REVENUE"],
        default_camp_revenue=app.config["BOOKING_DEFAULT_CAMP_REVENUE"],
    ),
    reminder_service=reminder_service,
    data_store=data_store,
)


@app.before_serving
async def startup():
    reminder_service.start()


@app.after_serving
async def shutdown():
    await reminder_service.shutdown()


@app.route("/acs/incomingcall", methods=["POST"])
async def incoming_call_handler():
    """Handles initial incoming call event from EventGrid."""
    events = await request.get_json()
    host_url = request.host_url.replace("http://", "https://", 1).rstrip("/")
    return await acs_handler.process_incoming_call(events, host_url, app.config)


@app.route("/acs/callbacks/<context_id>", methods=["POST"])
async def acs_event_callbacks(context_id):
    """Handles ACS event callbacks for call connection and streaming events."""
    raw_events = await request.get_json()
    return await acs_handler.process_callback_events(context_id, raw_events, app.config)


@app.websocket("/acs/ws")
async def acs_ws():
    logger = logging.getLogger("acs_ws")
    logger.info("Incoming ACS WebSocket connection")

    # Extract customer_id from query parameters
    customer_id = websocket.args.get("customerId", "default")   # <-- change
    logger.info("ACS WebSocket connection for customer: %s", customer_id)

    handler = ACSMediaHandler(app.config, customer_id=customer_id)
    await handler.init_incoming_websocket(websocket, is_raw_audio=False)
    asyncio.create_task(handler.connect())
    try:
        while True:
            msg = await websocket.receive()
            await handler.acs_to_voicelive(msg)
    except Exception:
        logger.exception("ACS WebSocket connection closed")
    finally:
        await handler.close()


@app.websocket("/web/ws")
async def web_ws():
    logger = logging.getLogger("web_ws")
    logger.info("Incoming Web WebSocket connection")

    # Extract customer_id from query parameters
    customer_id = websocket.args.get("customerId", "default")   # <-- change
    logger.info("Web WebSocket connection for customer: %s", customer_id)

    handler = ACSMediaHandler(app.config, customer_id=customer_id)
    await handler.init_incoming_websocket(websocket, is_raw_audio=True)
    asyncio.create_task(handler.connect())
    try:
        while True:
            msg = await websocket.receive()
            await handler.web_to_voicelive(msg)
    except Exception:
        logger.exception("Web WebSocket connection closed")
    finally:
        await handler.close()


@app.route("/")
async def index():
    """Redirect root to the booking SPA that includes admin pages/menu."""
    return redirect("/booking")


@app.route("/web-demo")
async def web_demo():
    """Serves the legacy web demo page."""
    return await app.send_static_file("index.html")


@app.route("/booking")
@app.route("/booking/<path:path>")
async def booking_app(path=""):
    """Serves the React booking frontend."""
    booking_dir = Path(app.static_folder) / "booking"

    # If booking assets are missing from image, return actionable error.
    if not (booking_dir / "index.html").exists():
        return "Booking app not built yet. Run 'npm run build' in the frontend directory.", 404

    # Serve concrete files from the booking bundle (assets, icons, etc).
    if path and (booking_dir / path).is_file():
        return await send_from_directory(booking_dir, path)

    # For client-side routes under /booking, serve SPA entrypoint.
    return await send_from_directory(booking_dir, "index.html")


@app.route("/api/bookings/availability", methods=["GET"])
async def booking_availability():
    if not booking_service.is_enabled():
        return jsonify({"error": "Booking integrations are not configured."}), 500

    customer_id = request.args.get("customerId", "default")
    start_iso = request.args.get("start")
    end_iso = request.args.get("end")
    if not start_iso or not end_iso:
        return jsonify({"error": "Query parameters 'start' and 'end' are required."}), 400

    try:
        result = booking_service.check_availability(customer_id, start_iso, end_iso)
        return jsonify(result), 200
    except Exception as exc:
        logging.getLogger("booking_api").exception("Availability check failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/bookings", methods=["POST"])
async def create_booking():
    if not booking_service.is_enabled():
        return jsonify({"error": "Booking integrations are not configured."}), 500

    payload = await request.get_json()
    if not payload:
        return jsonify({"error": "JSON payload is required."}), 400

    try:
        result = booking_service.create_booking(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logging.getLogger("booking_api").exception("Create booking failed")
        return jsonify({"error": str(exc)}), 500

    status = result.get("status")
    if status == "conflict":
        return jsonify(result), 409
    if status == "partial":
        return jsonify(result), 207
    return jsonify(result), 201


@app.route("/api/admin/bookings", methods=["GET"])
async def admin_bookings():
    limit = int(request.args.get("limit", "300"))
    return jsonify({"items": data_store.list_bookings(limit=limit)}), 200


@app.route("/api/admin/calls", methods=["GET"])
async def admin_calls():
    limit = int(request.args.get("limit", "300"))
    return jsonify({"items": data_store.list_calls(limit=limit)}), 200


@app.route("/api/admin/reports/summary", methods=["GET"])
async def admin_reports_summary():
    days = int(request.args.get("days", "30"))
    return jsonify(data_store.summary(days=days)), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
