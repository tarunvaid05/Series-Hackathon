"""HTTP client for Series Messaging API."""

import logging
from typing import List, Optional

import requests
from sems.config import API_BASE_URL, API_KEY, SENDER_NUMBER

logger = logging.getLogger(__name__)


def send_message(phone_number: str, text: str) -> dict:
    """
    Send a message to a phone number via the Series Messaging API.
    Creates a new chat and sends the message.

    Args:
        phone_number: E.164 format phone number (e.g., "+17187758176")
        text: Message text to send

    Returns:
        API response as dict
    """
    url = f"{API_BASE_URL}/api/chats"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "chat": {
            "phone_numbers": [phone_number]
        },
        "message": {
            "text": text
        },
        "send_from": SENDER_NUMBER,
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message to {phone_number}: {e}")
        return {"error": str(e)}


def create_group_chat(phone_numbers: List[str], display_name: str, message: str) -> dict:
    """Create a group chat with multiple participants and send welcome message.

    Args:
        phone_numbers: List of participant phone numbers (excluding sender)
        display_name: Chat name (event title)
        message: Welcome message to send

    Returns:
        API response dict containing 'chat_id' key, or error dict
    """
    url = f"{API_BASE_URL}/api/chats"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "send_from": SENDER_NUMBER,
        "chat": {
            "display_name": display_name,
            "phone_numbers": phone_numbers,
        },
        "message": {
            "text": message,
        },
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Extract chat_id from response - API returns data.id as the chat ID
        chat_id = data.get("data", {}).get("id")
        logger.info(f"Created group chat '{display_name}' with chat_id: {chat_id}")
        return {"chat_id": chat_id, **data}
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create group chat '{display_name}': {e}")
        return {"error": str(e)}


def send_message_to_chat(chat_id: int, text: str) -> dict:
    """Send a message to a specific chat by chat_id.

    Args:
        chat_id: The chat ID to send the message to
        text: Message text to send

    Returns:
        API response dict or error dict
    """
    url = f"{API_BASE_URL}/api/chats/{chat_id}/chat_messages"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "message": {
            "text": text,
        },
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message to chat {chat_id}: {e}")
        return {"error": str(e)}


def get_chat_id(phone_number: str) -> Optional[int]:
    """
    Get the chat ID for a given phone number.

    Args:
        phone_number: E.164 format phone number (e.g., "+17187758176")

    Returns:
        Chat ID if found, None otherwise
    """
    url = f"{API_BASE_URL}/api/chats"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    params = {"phone_number": phone_number}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        # API returns {"data": [...], "meta": {...}}
        chats = data.get("data", [])
        if chats and len(chats) > 0:
            return chats[0].get("id")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get chat ID for {phone_number}: {e}")
        return None


def start_typing(chat_id: int) -> bool:
    """
    Start typing indicator for a chat.

    Args:
        chat_id: The chat ID to show typing indicator for

    Returns:
        True on success, False on failure
    """
    url = f"{API_BASE_URL}/api/chats/{chat_id}/start_typing"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to start typing for chat {chat_id}: {e}")
        return False


def stop_typing(chat_id: int) -> bool:
    """
    Stop typing indicator for a chat.

    Args:
        chat_id: The chat ID to stop typing indicator for

    Returns:
        True on success, False on failure
    """
    url = f"{API_BASE_URL}/api/chats/{chat_id}/stop_typing"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to stop typing for chat {chat_id}: {e}")
        return False
