"""Message processor - orchestrates inbound message handling and responses."""

import logging
from sems.intent_handler import process_message
from sems.messaging_client import send_message, send_message_to_chat
from sems import event_store
from sems.group_chat_bot import handle_group_chat_message

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
        chat_id = data.get("chat_id")

        if not phone_number or not text:
            logger.warning(f"Missing phone_number or text in message: {kafka_message}")
            return

        # Check if this is a group chat message
        if chat_id:
            # Try to parse chat_id as int for comparison
            try:
                chat_id_int = int(chat_id)
            except (ValueError, TypeError):
                chat_id_int = None

            if chat_id_int:
                # Check if this chat_id belongs to an event group chat
                event = event_store.get_event_by_group_chat_id(chat_id_int)
                if event:
                    logger.info(f"Group chat message from {phone_number} in chat {chat_id}: {text}")

                    # Route to group chat bot handler
                    response = handle_group_chat_message(chat_id_int, phone_number, text)

                    if response:
                        logger.info(f"Group chat bot responding: {response}")
                        result = send_message_to_chat(chat_id_int, response)
                        logger.info(f"Group chat message sent, API response: {result}")
                    else:
                        logger.debug(f"Group chat message ignored (no bot response needed)")

                    return  # Don't process as regular 1:1 message

        logger.info(f"Processing message from {phone_number}: {text}")

        # Process through intent handler (1:1 messages)
        response = process_message(phone_number, text)

        logger.info(f"Sending response to {phone_number}: {response}")

        # Send response via messaging API
        result = send_message(phone_number, response)

        logger.info(f"Message sent, API response: {result}")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
