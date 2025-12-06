"""
Group Chat Bot Module for SEMS (Series Events Messaging System)

Handles bot responses in event group chats:
- When/where question detection (AI-powered)
- Time simulation for demo purposes
- Event reminder logic
"""

import os
import re
import logging
from typing import Optional
from datetime import datetime, timedelta

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from sems import event_store

logger = logging.getLogger(__name__)


class WhenWhereDetection(BaseModel):
    """Schema for when/where question detection."""
    is_when_where_question: bool = Field(
        description="True if user is asking about when or where the event is"
    )
    confidence: float = Field(
        default=0.8,
        description="Confidence score from 0.0 to 1.0"
    )


# Time simulation pattern: "X days pass", "X week later", etc.
TIME_SIMULATION_PATTERN = re.compile(
    r"(\d+)\s*(day|days|week|weeks|hour|hours)\s*(pass|later|passes)",
    re.IGNORECASE
)

# Month name mapping for date parsing
MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}

# Pattern to extract "Month Dayth" format (e.g., "December 25th", "January 1st")
DATE_PATTERN = re.compile(
    r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?",
    re.IGNORECASE
)


def parse_event_date(datetime_str: str) -> Optional[datetime]:
    """
    Parse event datetime string to extract the date.
    
    Handles formats like "December 25th", "December 25th at 7", etc.
    
    Args:
        datetime_str: The event's datetime string
        
    Returns:
        datetime object if parsed successfully, None otherwise
    """
    if not datetime_str:
        return None
    
    match = DATE_PATTERN.search(datetime_str.lower())
    if not match:
        return None
    
    month_name = match.group(1).lower()
    day = int(match.group(2))
    month = MONTH_MAP.get(month_name)
    
    if not month:
        return None
    
    # Use current year, or next year if date has passed
    current = datetime.now()
    year = current.year
    
    try:
        event_date = datetime(year, month, day)
        # If the date is in the past, assume next year
        if event_date < current:
            event_date = datetime(year + 1, month, day)
        return event_date
    except ValueError:
        return None


def detect_when_where_question(message: str) -> bool:
    """
    Use AI to detect if message is asking about when/where the event is.

    Args:
        message: The user message to analyze

    Returns:
        True if the message is a when/where question
    """
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )

        structured_llm = llm.with_structured_output(WhenWhereDetection)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Determine if the user is asking about WHEN or WHERE an event is happening.

Examples of when/where questions (return True):
- "When is this again?"
- "Where are we meeting?"
- "What time does this start?"
- "What's the location?"
- "When and where?"
- "Remind me of the details"
- "When's the event?"
- "Where's it at?"
- "What time?"
- "Location?"

NOT when/where questions (return False):
- General conversation
- "I'll be late"
- "See you there"
- "Who's coming?"
- Any other topic

Be decisive. Only return True for clear when/where questions."""),
            ("human", "{message}")
        ])

        chain = prompt | structured_llm
        result = chain.invoke({"message": message})

        return result.is_when_where_question and result.confidence >= 0.7

    except Exception as e:
        logger.error(f"AI detection failed: {e}")
        # Fallback to simple keyword matching
        keywords = ["when", "where", "time", "location", "place", "what time", "details"]
        message_lower = message.lower()
        return any(kw in message_lower for kw in keywords)


def parse_time_simulation(message: str) -> Optional[timedelta]:
    """
    Parse time simulation commands like "15 days pass", "1 week later".

    Args:
        message: The user message

    Returns:
        timedelta if time simulation command detected, None otherwise
    """
    match = TIME_SIMULATION_PATTERN.search(message)
    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2).lower()

    if unit in ("day", "days"):
        return timedelta(days=amount)
    elif unit in ("week", "weeks"):
        return timedelta(weeks=amount)
    elif unit in ("hour", "hours"):
        return timedelta(hours=amount)

    return None


def get_triggered_reminders(event: dict, days_until_event: int, prev_days_until: int) -> list[str]:
    """
    Calculate which reminders should be triggered based on days until event.
    
    Only returns reminders that cross a threshold between prev_days_until and days_until_event.
    
    Reminder thresholds (days before event):
    - 7 days before (1 week)
    - 3 days before
    - 1 day before
    - 0 days (day of event)

    Args:
        event: The event dict
        days_until_event: Current days until the event (after time simulation)
        prev_days_until: Previous days until the event (before this time simulation)

    Returns:
        List of reminder messages that would have been triggered
    """
    reminders = []
    event_title = event.get("title", "Event")
    event_datetime = event.get("datetime", "TBD")
    event_location = event.get("location", "TBD")

    # Define reminder thresholds (days before event) and their labels
    thresholds = [
        (7, "1 week"),
        (3, "3 days"),
        (1, "1 day"),
        (0, "TODAY"),
    ]

    # Check which thresholds we crossed
    for threshold_days, label in thresholds:
        # A reminder fires if:
        # - We were above this threshold before (prev_days_until > threshold_days)
        # - We are now at or below this threshold (days_until_event <= threshold_days)
        if prev_days_until > threshold_days >= days_until_event:
            if threshold_days == 0:
                time_msg = "is TODAY"
            else:
                time_msg = f"is in {label}"
            
            reminder = (
                f"⏰ Reminder: {event_title} {time_msg}!\n\n"
                f"When: {event_datetime}\n"
                f"Where: {event_location}"
            )
            reminders.append(reminder)

    # 1 hour before reminder - fires when we reach day of event
    # (simplified: triggers along with the "TODAY" reminder)
    if prev_days_until > 0 >= days_until_event:
        reminder = (
            f"⏰ Reminder: {event_title} starts in 1 hour!\n\n"
            f"When: {event_datetime}\n"
            f"Where: {event_location}"
        )
        reminders.append(reminder)

    return reminders


def format_when_where_response(event: dict) -> str:
    """
    Format the when/where response for an event.

    Args:
        event: The event dict

    Returns:
        Formatted response string
    """
    event_datetime = event.get("datetime", "TBD")
    event_location = event.get("location", "TBD")

    return f"When: {event_datetime}\nWhere: {event_location}"


def handle_group_chat_message(chat_id: int, phone_number: str, message: str) -> Optional[str]:
    """
    Handle a message from a group chat.

    Only responds to:
    - When/where questions
    - Time simulation commands

    Args:
        chat_id: The group chat ID
        phone_number: The sender's phone number
        message: The message text

    Returns:
        Response string if bot should respond, None to ignore
    """
    # Find the event for this group chat
    event = event_store.get_event_by_group_chat_id(chat_id)
    if not event:
        logger.warning(f"No event found for group chat {chat_id}")
        return None

    event_id = event.get("id")

    # Check for time simulation command first
    time_passed = parse_time_simulation(message)
    if time_passed:
        # Parse the event date
        event_datetime_str = event.get("datetime", "")
        event_date = parse_event_date(event_datetime_str)
        
        if not event_date:
            return f"Could not parse event date from '{event_datetime_str}'. Use format like 'December 25th'."
        
        # Get current simulated days and calculate days until event
        simulated_days = event_store.get_simulated_days(event_id)
        today = datetime.now()
        
        # Calculate the "simulated today" by adding simulated days to real today
        simulated_today = today + timedelta(days=simulated_days)
        prev_days_until = (event_date - simulated_today).days
        
        # Add the new time passage
        days_to_add = time_passed.days
        new_simulated_days = event_store.add_simulated_days(event_id, days_to_add)
        
        # Calculate new simulated date and days until event
        new_simulated_today = today + timedelta(days=new_simulated_days)
        days_until_event = (event_date - new_simulated_today).days
        
        # Get reminders that should trigger
        reminders = get_triggered_reminders(event, days_until_event, prev_days_until)
        
        # Build response
        status_msg = f"📅 Simulated {days_to_add} days passing. Now {new_simulated_days} days from start."
        
        if days_until_event > 0:
            status_msg += f"\n{days_until_event} days until {event.get('title', 'event')}."
        elif days_until_event == 0:
            status_msg += f"\n{event.get('title', 'Event')} is TODAY!"
        else:
            status_msg += f"\n{event.get('title', 'Event')} was {abs(days_until_event)} days ago."
        
        if reminders:
            return status_msg + "\n\n---\n\n" + "\n\n---\n\n".join(reminders)
        else:
            return status_msg + "\n\nNo new reminders triggered."

    # Check for when/where question
    if detect_when_where_question(message):
        return format_when_where_response(event)

    # Ignore all other messages
    return None
