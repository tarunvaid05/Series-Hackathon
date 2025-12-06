"""HTTP client for Series Messaging API."""

import logging
from typing import List

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
        API response dict or error dict
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
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create group chat '{display_name}': {e}")
        return {"error": str(e)}
