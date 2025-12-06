"""Intent detection and conversational flow logic for SEMS."""

from sems import state_store

# Intent keywords (Section 3.1: keyword matching is sufficient)
CREATE_INTENTS = ["create event", "new event", "host an event", "make an event", "schedule an event", "plan an event"]
CANCEL_KEYWORDS = ["cancel"]
RESTART_KEYWORDS = ["restart"]
CONFIRM_KEYWORDS = ["confirm", "yes"]
SKIP_KEYWORDS = ["skip", "none", "no"]

# Prompts for each step
PROMPTS = {
    "title": "What's the title of your event?",
    "description": "Got it! Now give me a brief description of the event.",
    "datetime": "When is this event? (date and time)",
    "location": "Where will it be held?",
    "capacity": "How many people can attend? (or say 'skip' for no limit)",
    "confirm": None  # Special handling - shows summary
}


def detect_intent(text: str) -> str:
    """
    Detect the intent from user message.
    Returns: "create_event", "cancel", "restart", "confirm", "skip", or "input"
    """
    text_lower = text.lower().strip()

    # Check for cancel first (can happen anytime)
    for keyword in CANCEL_KEYWORDS:
        if keyword in text_lower:
            return "cancel"

    # Check for restart
    for keyword in RESTART_KEYWORDS:
        if keyword in text_lower:
            return "restart"

    # Check for create event intent
    for phrase in CREATE_INTENTS:
        if phrase in text_lower:
            return "create_event"

    # Check for confirm
    for keyword in CONFIRM_KEYWORDS:
        if text_lower == keyword or text_lower.startswith(keyword):
            return "confirm"

    # Check for skip
    for keyword in SKIP_KEYWORDS:
        if text_lower == keyword:
            return "skip"

    # Default: treat as input for current step
    return "input"


def format_summary(event: dict) -> str:
    """Format event data as a summary for confirmation."""
    capacity_str = event["capacity"] if event["capacity"] else "No limit"
    return f"""Here's your event summary:

Title: {event["title"]}
Description: {event["description"]}
When: {event["datetime"]}
Where: {event["location"]}
Capacity: {capacity_str}

Reply 'confirm' to create or 'restart' to start over."""


def process_message(phone_number: str, text: str) -> str:
    """
    Process an incoming message and return the response.

    This is the main flow logic per Project-Requirements.txt Section 3 and 5.
    """
    intent = detect_intent(text)
    state = state_store.get_state(phone_number)

    # Handle cancel - always works
    if intent == "cancel":
        state_store.clear_state(phone_number)
        return "Event creation cancelled. Text 'create event' anytime to start again."

    # Handle restart - always works
    if intent == "restart":
        state_store.clear_state(phone_number)
        state_store.start_flow(phone_number)
        return PROMPTS["title"]

    # Not in a flow - check for create intent
    if state is None:
        if intent == "create_event":
            state_store.start_flow(phone_number)
            return PROMPTS["title"]
        else:
            return "Hi! Text 'create event' to start creating a new event."

    # In a flow - process based on current step
    current_step = state["step"]

    # Handle confirmation step
    if current_step == "confirm":
        if intent == "confirm":
            event = state_store.get_event_data(phone_number)
            state_store.clear_state(phone_number)
            return f"Event created! Your event '{event['title']}' is all set."
        else:
            # Re-show summary if they didn't confirm
            event = state_store.get_event_data(phone_number)
            return format_summary(event)

    # Handle capacity step (can be skipped)
    if current_step == "capacity":
        if intent == "skip":
            state_store.update_state(phone_number, "capacity", None)
        else:
            state_store.update_state(phone_number, "capacity", text.strip())
        # Show summary
        event = state_store.get_event_data(phone_number)
        return format_summary(event)

    # Handle other steps - store the input and move to next
    state_store.update_state(phone_number, current_step, text.strip())

    # Get next step's prompt
    new_state = state_store.get_state(phone_number)
    next_step = new_state["step"]

    if next_step == "confirm":
        event = state_store.get_event_data(phone_number)
        return format_summary(event)

    return PROMPTS[next_step]
