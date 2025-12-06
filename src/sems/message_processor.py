"""Message processor - orchestrates inbound message handling and responses."""

import logging
from sems.intent_handler import process_message
from sems.messaging_client import send_message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def handle_kafka_message(kafka_message: dict) -> None:
    """
    Handle an inbound Kafka message.

    Kafka message structure (v2 API):
    {
        "api_version": "v2",
        "event_type": "message.received",  # Only process this type
        "data": {
            "from_phone": "+17187758176",
            "text": "user message text",
            "chat_id": "1702232",
            ...
        }
    }
    """
    try:
        # Only process message.received events
        event_type = kafka_message.get("event_type")
        if event_type != "message.received":
            logger.debug(f"Ignoring event type: {event_type}")
            return

        data = kafka_message.get("data", {})
        phone_number = data.get("from_phone")
        text = data.get("text")

        if not phone_number or not text:
            logger.warning(f"Missing phone_number or text in message: {kafka_message}")
            return

        logger.info(f"Processing message from {phone_number}: {text}")

        # Process through intent handler
        response = process_message(phone_number, text)

        logger.info(f"Sending response to {phone_number}: {response}")

        # Send response via messaging API
        result = send_message(phone_number, response)

        logger.info(f"Message sent, API response: {result}")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
