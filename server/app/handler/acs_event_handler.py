"""Handler for processing ACS (Azure Communication Services) call and callback events."""

import json
import logging
import uuid
from pathlib import Path
from urllib.parse import urlencode, urlparse, urlunparse

from azure.communication.callautomation import (AudioFormat,
                                                MediaStreamingAudioChannelType,
                                                MediaStreamingContentType,
                                                MediaStreamingOptions,
                                                StreamingTransportType)
from azure.communication.callautomation.aio import CallAutomationClient
from azure.eventgrid import EventGridEvent, SystemEventNames
from quart import Response

logger = logging.getLogger(__name__)


def load_customer_routing() -> dict:
    """
    Load customer routing configuration from JSON file.

    Returns:
        Dictionary with customer routing config
    """
    handler_dir = Path(__file__).parent
    routing_path = handler_dir.parent.parent / "customer_routing.json"

    try:
        with open(routing_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            logger.info("[AcsEventHandler] Loaded customer routing config with %d customers",
                       len(config.get("customers", {})))
            return config
    except FileNotFoundError:
        logger.warning("[AcsEventHandler] customer_routing.json not found, using default routing")
        return {"customers": {}, "default": {"customer_id": "default", "prompt_file": "grace_intake_agent.txt"}}
    except Exception as e:
        logger.exception("[AcsEventHandler] Error loading customer routing: %s", e)
        return {"customers": {}, "default": {"customer_id": "default", "prompt_file": "grace_intake_agent.txt"}}


def get_customer_config(to_phone_number: str, routing_config: dict) -> dict:
    """
    Get customer configuration based on the called phone number.

    Args:
        to_phone_number: The phone number that was called (e.g., "+18005551234")
        routing_config: The routing configuration dictionary

    Returns:
        Customer configuration with customer_id, prompt_file, etc.
    """
    # Normalize phone number (remove spaces, dashes)
    normalized = to_phone_number.replace(" ", "").replace("-", "")

    customers = routing_config.get("customers", {})

    # Try exact match first
    if normalized in customers:
        config = customers[normalized]
        logger.info("[AcsEventHandler] Matched customer: %s (phone: %s)",
                   config.get("customer_name", "Unknown"), normalized)
        return config

    # Try without country code prefix variations
    for phone_key, config in customers.items():
        if normalized.endswith(phone_key[-10:]) or phone_key.endswith(normalized[-10:]):
            logger.info("[AcsEventHandler] Partial match for customer: %s (phone: %s)",
                       config.get("customer_name", "Unknown"), phone_key)
            return config

    # Use default
    default_config = routing_config.get("default", {"customer_id": "default", "prompt_file": "grace_intake_agent.txt"})
    logger.info("[AcsEventHandler] No customer match for %s, using default", normalized)
    return default_config


class AcsEventHandler:
    """Handles ACS event processing and call answering logic."""

    def __init__(self, config):
        self.acs_client = CallAutomationClient.from_connection_string(
            config["ACS_CONNECTION_STRING"]
        )

    async def process_incoming_call(self, events: list, host_url, config):
        """Processes incoming call events and answers calls with media streaming."""
        logger.info("incoming event data")

        for event_dict in events:
            event = EventGridEvent.from_dict(event_dict)
            logger.info("incoming event data --> %s", event.data)

            if (
                event.event_type
                == SystemEventNames.EventGridSubscriptionValidationEventName
            ):
                logger.info("Validating subscription")
                validation_code = event.data["validationCode"]
                return Response(
                    response=json.dumps({"validationResponse": validation_code}),
                    status=200,
                )

            if event.event_type == "Microsoft.Communication.IncomingCall":
                logger.info("Incoming call received: data=%s", event.data)

                caller_info = event.data["from"]
                caller_id = (
                    caller_info["phoneNumber"]["value"]
                    if caller_info["kind"] == "phoneNumber"
                    else caller_info["rawId"]
                )

                # Extract the phone number that was called (to_phone_number)
                to_info = event.data.get("to", {})
                to_phone_number = (
                    to_info.get("phoneNumber", {}).get("value")
                    if to_info.get("kind") == "phoneNumber"
                    else to_info.get("rawId", "unknown")
                )

                logger.info("incoming call handler caller id: %s, called number: %s", caller_id, to_phone_number)

                # Load customer routing and determine customer configuration
                routing_config = load_customer_routing()
                customer_config = get_customer_config(to_phone_number, routing_config)
                customer_id = customer_config.get("customer_id", "default")

                logger.info("Routing call to customer: %s", customer_id)

                incoming_call_context = event.data["incomingCallContext"]
                query_parameters = urlencode({"callerId": caller_id, "customerId": customer_id})
                guid = uuid.uuid4()

                callback_events_uri = (
                    f"{config['ACS_DEV_TUNNEL']}/acs/callbacks"
                    if config["ACS_DEV_TUNNEL"]
                    else f"{host_url}/acs/callbacks"
                )
                callback_uri = f"{callback_events_uri}/{guid}?{query_parameters}"

                parsed_url = urlparse(callback_events_uri)
                websocket_url = urlunparse(
                    ("wss", parsed_url.netloc, "/acs/ws", "", "", "")
                )

                logger.info("callback url: %s", callback_uri)
                logger.info("websocket url: %s", websocket_url)

                media_streaming_options = MediaStreamingOptions(
                    transport_url=websocket_url,
                    transport_type=StreamingTransportType.WEBSOCKET,
                    content_type=MediaStreamingContentType.AUDIO,
                    audio_channel_type=MediaStreamingAudioChannelType.MIXED,
                    start_media_streaming=True,
                    enable_bidirectional=True,
                    audio_format=AudioFormat.PCM24_K_MONO,
                )

                result = await self.acs_client.answer_call(
                    incoming_call_context=incoming_call_context,
                    operation_context="incomingCall",
                    callback_url=callback_uri,
                    media_streaming=media_streaming_options,
                )

                logger.info(
                    "Answered call for connection id: %s", result.call_connection_id
                )
                return Response(status=200)

        return Response(status=400)

    async def process_callback_events(self, context_id: str, raw_events: list, config):
        """Processes ACS callback events such as call connected, media started, etc."""
        for event in raw_events:
            event_data = event["data"]
            call_connection_id = event_data["callConnectionId"]

            logger.info(
                "Received Event:-> %s, Correlation Id:-> %s, CallConnectionId:-> %s",
                event["type"],
                event_data["correlationId"],
                call_connection_id,
            )

            if event["type"] == "Microsoft.Communication.CallConnected":
                properties = await self.acs_client.get_call_connection(
                    call_connection_id
                ).get_call_properties()

                logger.info(
                    "MediaStreamingSubscription:--> %s",
                    properties.media_streaming_subscription,
                )
                logger.info(
                    "Received CallConnected event for connection id: %s",
                    call_connection_id,
                )
                logger.info("CORRELATION ID:--> %s", event_data["correlationId"])
                logger.info("CALL CONNECTION ID:--> %s", call_connection_id)

            elif event["type"] == "Microsoft.Communication.MediaStreamingStarted":
                update = event_data["mediaStreamingUpdate"]
                logger.info(
                    "Media streaming content type:--> %s", update["contentType"]
                )
                logger.info(
                    "Media streaming status:--> %s", update["mediaStreamingStatus"]
                )
                logger.info(
                    "Media streaming status details:--> %s",
                    update["mediaStreamingStatusDetails"],
                )

            elif event["type"] == "Microsoft.Communication.MediaStreamingStopped":
                update = event_data["mediaStreamingUpdate"]
                logger.info(
                    "Media streaming content type:--> %s", update["contentType"]
                )
                logger.info(
                    "Media streaming status:--> %s", update["mediaStreamingStatus"]
                )
                logger.info(
                    "Media streaming status details:--> %s",
                    update["mediaStreamingStatusDetails"],
                )

            elif event["type"] == "Microsoft.Communication.MediaStreamingFailed":
                result_info = event_data["resultInformation"]
                logger.info(
                    "Code:-> %s, Subcode:-> %s",
                    result_info["code"],
                    result_info["subCode"],
                )
                logger.info("Message:-> %s", result_info["message"])

            elif event["type"] == "Microsoft.Communication.CallDisconnected":
                logger.info(
                    "CallDisconnected event received for: %s", call_connection_id
                )

        return Response(status=200)
