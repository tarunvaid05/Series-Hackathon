"""Intent detection and conversational flow logic for SEMS."""

from typing import List, Optional, Tuple

from sems import state_store, event_store, user_store
from sems.messaging_client import send_message, create_group_chat

# Intent keywords (Section 3.1: keyword matching is sufficient)
CREATE_INTENTS = ["create event", "new event", "host an event", "make an event", "schedule an event", "plan an event"]
CANCEL_KEYWORDS = ["cancel"]
RESTART_KEYWORDS = ["restart"]
CONFIRM_KEYWORDS = ["confirm", "yes"]
SKIP_KEYWORDS = ["skip", "none", "no"]

# Phase 2 intent keywords (Sections 12-16)
EDIT_INTENTS = ["edit event", "edit my event", "change my event", "modify event"]
JOIN_INTENTS = ["find events", "what's happening", "events near", "join event", "any events", "whats happening"]
LEAVE_INTENTS = ["leave event", "cancel rsvp", "drop out", "quit event"]
DELETE_INTENTS = ["delete event", "remove event", "delete my event"]
MY_EVENTS_INTENTS = ["my events", "my enrolled events", "enrolled events", "events i joined"]

# Phase 3 intent keywords (Sections 17-21)
CLOSE_INTENTS = ["close event", "close registration", "stop registration"]
APPROVE_PATTERN = "approve "  # "approve John"
DENY_PATTERN = "deny "  # "deny John"

# Prompts for create flow steps
PROMPTS = {
    "title": "What's the title of your event?",
    "description": "Got it! Now give me a brief description of the event.",
    "datetime": "When is this event? (date and time)",
    "location": "Where will it be held?",
    "capacity": "How many people can attend? (not including yourself, or 'skip' for no limit)",
    "confirm": None  # Special handling - shows summary
}

# Phase 2 flow prompts (Sections 12-16)
EDIT_PROMPTS = {
    "select_event": "Which event would you like to edit? Reply with the number.",
    "select_field": "Which field would you like to change?\n1. Title\n2. Description\n3. Date/Time\n4. Location\n5. Capacity\n\nReply with a number or 'done' to finish.",
    "new_value": "Enter the new {field}:"
}
JOIN_PROMPTS = {
    "select_event": "Which event would you like to join? Reply with the number."
}
LEAVE_PROMPTS = {
    "select_event": "Which event would you like to leave? Reply with the number."
}
DELETE_PROMPTS = {
    "select_event": "Which event would you like to delete? Reply with the number.",
    "confirm_delete": "Are you sure you want to delete '{title}'? Reply 'yes' to confirm."
}

# Phase 3 flow prompts (Sections 17-21)
REGISTER_PROMPTS = {
    "get_name": "Welcome to SEMS! What's your name?"
}
CLOSE_PROMPTS = {
    "select_event": "Which event would you like to close? Reply with the number.",
    "confirm_groupchat": "Would you like to create a group chat with all participants? (yes/no)"
}

# Field name mapping for edit flow
EDIT_FIELDS = {
    "1": "title",
    "2": "description",
    "3": "datetime",
    "4": "location",
    "5": "capacity"
}
FIELD_DISPLAY_NAMES = {
    "title": "title",
    "description": "description",
    "datetime": "date/time",
    "location": "location",
    "capacity": "capacity"
}


def detect_intent(text: str) -> Tuple[str, Optional[str]]:
    """
    Detect the intent from user message.
    Returns: Tuple of (intent, extracted_name)
        - intent: "create_event", "edit_event", "join_event", "leave_event", "delete_event",
                  "close_event", "approve", "deny", "cancel", "restart", "confirm", "skip", or "input"
        - extracted_name: Name extracted from approve/deny commands, or None

    IMPORTANT: Check longer phrases first to avoid conflicts.
    DELETE_INTENTS checked before CANCEL_KEYWORDS to prevent "delete event" matching "cancel".
    """
    text_lower = text.lower().strip()

    # Check for restart first
    for keyword in RESTART_KEYWORDS:
        if keyword in text_lower:
            return ("restart", None)

    # Check DELETE_INTENTS before cancel to avoid "delete event" matching "cancel"
    for phrase in DELETE_INTENTS:
        if phrase in text_lower:
            return ("delete_event", None)

    # Check for cancel (can happen anytime)
    for keyword in CANCEL_KEYWORDS:
        if keyword in text_lower:
            return ("cancel", None)

    # Check for create event intent
    for phrase in CREATE_INTENTS:
        if phrase in text_lower:
            return ("create_event", None)

    # Check for edit event intent
    for phrase in EDIT_INTENTS:
        if phrase in text_lower:
            return ("edit_event", None)

    # Check for close event intent (Phase 3)
    for phrase in CLOSE_INTENTS:
        if phrase in text_lower:
            return ("close_event", None)

    # Check for approve pattern (Phase 3) - "approve John"
    if text_lower.startswith(APPROVE_PATTERN):
        name = text[len(APPROVE_PATTERN):].strip()
        return ("approve", name if name else None)

    # Check for deny pattern (Phase 3) - "deny John"
    if text_lower.startswith(DENY_PATTERN):
        name = text[len(DENY_PATTERN):].strip()
        return ("deny", name if name else None)

    # Check for join/discover event intent
    for phrase in JOIN_INTENTS:
        if phrase in text_lower:
            return ("join_event", None)

    # Check for leave event intent
    for phrase in LEAVE_INTENTS:
        if phrase in text_lower:
            return ("leave_event", None)

    # Check for my enrolled events intent
    for phrase in MY_EVENTS_INTENTS:
        if phrase in text_lower:
            return ("my_events", None)

    # Check for confirm
    for keyword in CONFIRM_KEYWORDS:
        if text_lower == keyword or text_lower.startswith(keyword):
            return ("confirm", None)

    # Check for skip
    for keyword in SKIP_KEYWORDS:
        if text_lower == keyword:
            return ("skip", None)

    # Default: treat as input for current step
    return ("input", None)


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


def format_event_list(events: List[dict], show_spots: bool = True) -> str:
    """
    Format a list of events for display (joinable events).
    Per Section 16.2: Event Display Format.
    """
    if not events:
        return ""

    lines = []
    for i, event in enumerate(events, 1):
        capacity = event.get("capacity")
        participants = event.get("participants", [])
        current_count = len(participants)

        if show_spots:
            if capacity is not None:
                try:
                    spots_str = f"{current_count}/{capacity}"
                except (ValueError, TypeError):
                    spots_str = "unlimited"
            else:
                spots_str = "unlimited"

            lines.append(
                f"{i}. {event['title']}\n"
                f"   When: {event['datetime']}\n"
                f"   Where: {event['location']}\n"
                f"   Spots: {spots_str}"
            )
        else:
            lines.append(
                f"{i}. {event['title']}\n"
                f"   When: {event['datetime']}\n"
                f"   Where: {event['location']}"
            )

    return "\n\n".join(lines)


def format_hosted_events(events: List[dict]) -> str:
    """
    Format events for edit/delete selection (simpler format).
    Per Section 16.1: Number lists for selection.
    """
    if not events:
        return ""

    lines = []
    for i, event in enumerate(events, 1):
        lines.append(f"{i}. {event['title']} ({event['datetime']})")

    return "\n".join(lines)


def format_joined_events(events: List[dict]) -> str:
    """Format events the user has joined for leave selection."""
    if not events:
        return ""

    lines = []
    for i, event in enumerate(events, 1):
        lines.append(f"{i}. {event['title']} ({event['datetime']})")

    return "\n".join(lines)


def format_enrolled_events_with_host(events: List[dict], is_host: bool = False) -> str:
    """Format events with status (capacity or closed), optionally marking as host."""
    if not events:
        return ""

    lines = []
    for i, event in enumerate(events, 1):
        status = event.get("status", "open")
        if status == "closed":
            status_str = "(closed)"
        else:
            capacity = event.get("capacity")
            participants = event.get("participants", [])
            current_count = len(participants)
            if capacity is not None:
                try:
                    status_str = f"({current_count}/{int(capacity)})"
                except (ValueError, TypeError):
                    status_str = f"({current_count} joined)"
            else:
                status_str = f"({current_count} joined)"
        host_label = " (Host)" if is_host else ""
        lines.append(f"{i}. {event['title']} {status_str}{host_label}")

    return "\n".join(lines)


def format_event_details(event: dict) -> str:
    """Format a single event's full details (after edit)."""
    capacity = event.get("capacity")
    participants = event.get("participants", [])
    current_count = len(participants)

    if capacity is not None:
        capacity_str = f"{current_count}/{capacity} spots filled"
    else:
        capacity_str = f"{current_count} joined (no limit)"

    return f"""Event: {event['title']}
Description: {event['description']}
When: {event['datetime']}
Where: {event['location']}
Capacity: {capacity_str}"""


def process_message(phone_number: str, text: str) -> str:
    """
    Process an incoming message and return the response.

    This is the main flow logic per Project-Requirements.txt Sections 3, 5, 12-16, and 17-21.
    Handles create, edit, join, leave, delete, register, close, approve, and deny flows.
    """
    intent, extracted_name = detect_intent(text)
    state = state_store.get_state(phone_number)
    text_stripped = text.strip()

    # Handle cancel - always works (clears any flow)
    if intent == "cancel":
        state_store.clear_state(phone_number)
        return "Cancelled. Text 'create event' to make a new event, or 'find events' to see what's happening."

    # Handle restart - clears state and starts create flow
    if intent == "restart":
        state_store.clear_state(phone_number)
        # Check registration before starting create flow
        if not user_store.is_registered(phone_number):
            state_store.start_flow(phone_number, "register")
            state_store.set_pending_flow(phone_number, "create_event")
            return REGISTER_PROMPTS["get_name"]
        state_store.start_flow(phone_number, "create")
        return PROMPTS["title"]

    # --- PHASE 3: Handle approve/deny intents (host actions) ---
    if intent == "approve":
        return _handle_approve(phone_number, extracted_name)
    if intent == "deny":
        return _handle_deny(phone_number, extracted_name)

    # --- PHASE 3: Check if user needs to register first ---
    if not user_store.is_registered(phone_number):
        # Already in registration flow
        if state is not None and state.get("flow_type") == "register":
            return _handle_register_flow(phone_number, state, text_stripped)
        # Need to start registration for any actionable intent
        if intent in ["create_event", "edit_event", "join_event", "leave_event",
                      "delete_event", "close_event"]:
            state_store.start_flow(phone_number, "register")
            state_store.set_pending_flow(phone_number, intent)
            return REGISTER_PROMPTS["get_name"]
        # Default welcome for unregistered users
        if state is None:
            state_store.start_flow(phone_number, "register")
            return REGISTER_PROMPTS["get_name"]

    # --- NOT IN A FLOW: Check for intent to start a new flow ---
    if state is None:
        return _handle_new_intent(phone_number, intent)

    # --- IN A FLOW: Route to appropriate flow handler ---
    flow_type = state.get("flow_type", "create")

    if flow_type == "register":
        return _handle_register_flow(phone_number, state, text_stripped)
    elif flow_type == "create":
        return _handle_create_flow(phone_number, state, intent, text_stripped)
    elif flow_type == "edit":
        return _handle_edit_flow(phone_number, state, intent, text_stripped)
    elif flow_type == "join":
        return _handle_join_flow(phone_number, state, text_stripped)
    elif flow_type == "leave":
        return _handle_leave_flow(phone_number, state, text_stripped)
    elif flow_type == "delete":
        return _handle_delete_flow(phone_number, state, intent, text_stripped)
    elif flow_type == "close":
        return _handle_close_flow(phone_number, state, text_stripped)
    else:
        # Unknown flow type - clear and prompt
        state_store.clear_state(phone_number)
        return "Something went wrong. Text 'create event' to start fresh."


def _handle_new_intent(phone_number: str, intent: str) -> str:
    """Handle intents when user is not in any flow."""

    if intent == "create_event":
        state_store.start_flow(phone_number, "create")
        return PROMPTS["title"]

    elif intent == "edit_event":
        events = event_store.get_events_by_host(phone_number)
        if not events:
            return "You haven't created any events yet. Text 'create event' to get started!"
        state_store.start_flow(phone_number, "edit")
        event_list = format_hosted_events(events)
        return f"Your events:\n\n{event_list}\n\n{EDIT_PROMPTS['select_event']}"

    elif intent == "join_event":
        events = event_store.get_open_events_for_discovery(phone_number)
        if not events:
            return "No events available to join right now. Check back later or text 'create event' to host your own!"
        state_store.start_flow(phone_number, "join")
        event_list = format_event_list(events, show_spots=True)
        return f"Available events:\n\n{event_list}\n\n{JOIN_PROMPTS['select_event']}"

    elif intent == "leave_event":
        events = event_store.get_joined_events(phone_number)
        if not events:
            return "You haven't joined any events. Text 'find events' to see what's happening!"
        state_store.start_flow(phone_number, "leave")
        event_list = format_joined_events(events)
        return f"Events you've joined:\n\n{event_list}\n\n{LEAVE_PROMPTS['select_event']}"

    elif intent == "delete_event":
        events = event_store.get_events_by_host(phone_number)
        if not events:
            return "You haven't created any events to delete. Text 'create event' to get started!"
        state_store.start_flow(phone_number, "delete")
        event_list = format_hosted_events(events)
        return f"Your events:\n\n{event_list}\n\n{DELETE_PROMPTS['select_event']}"

    elif intent == "close_event":
        # Phase 3: Close event flow - only show open events
        events = [e for e in event_store.get_events_by_host(phone_number)
                  if e.get("status") == "open"]
        if not events:
            return "You don't have any open events to close. Text 'create event' to host one!"
        state_store.start_flow(phone_number, "close")
        event_list = format_hosted_events(events)
        return f"Your open events:\n\n{event_list}\n\n{CLOSE_PROMPTS['select_event']}"

    elif intent == "my_events":
        # Show hosted events and enrolled events with status
        hosted = event_store.get_events_by_host(phone_number)
        joined = event_store.get_joined_events(phone_number)
        if not hosted and not joined:
            return "You don't have any events yet. Text 'create event' to host one or 'find events' to join!"
        lines = []
        if hosted:
            lines.append("Your hosted events:")
            lines.append(format_enrolled_events_with_host(hosted, is_host=True))
        if joined:
            if hosted:
                lines.append("")
            lines.append("Events you've joined:")
            lines.append(format_enrolled_events_with_host(joined, is_host=False))
        return "\n".join(lines)

    else:
        # Default welcome message
        name = user_store.get_name(phone_number)
        greeting = f"Hi {name}!" if name else "Hi!"
        return (f"{greeting} Here's what you can do:\n"
                "- 'create event' to host a new event\n"
                "- 'find events' to see what's happening\n"
                "- 'my events' to see events you've joined\n"
                "- 'edit event' to modify your events\n"
                "- 'close event' to finalize your event\n"
                "- 'delete event' to remove your events")


def _handle_create_flow(phone_number: str, state: dict, intent: str, text: str) -> str:
    """Handle the create event flow."""
    current_step = state["step"]

    # Handle confirmation step
    if current_step == "confirm":
        if intent == "confirm":
            event_data = state_store.get_event_data(phone_number)
            # Persist the event to storage
            created_event = event_store.create_event(event_data)
            state_store.clear_state(phone_number)
            return f"Event created! Your event '{created_event['title']}' is all set. Share it with friends!"
        else:
            # Re-show summary if they didn't confirm
            event = state_store.get_event_data(phone_number)
            return format_summary(event)

    # Handle capacity step (can be skipped)
    if current_step == "capacity":
        if intent == "skip":
            state_store.update_state(phone_number, "capacity", None)
        else:
            # Try to parse as integer, but accept any text
            try:
                capacity_val = int(text)
                state_store.update_state(phone_number, "capacity", capacity_val)
            except ValueError:
                state_store.update_state(phone_number, "capacity", text)
        # Show summary
        event = state_store.get_event_data(phone_number)
        return format_summary(event)

    # Handle other steps - store the input and move to next
    state_store.update_state(phone_number, current_step, text)

    # Get next step's prompt
    new_state = state_store.get_state(phone_number)
    next_step = new_state["step"]

    if next_step == "confirm":
        event = state_store.get_event_data(phone_number)
        return format_summary(event)

    return PROMPTS[next_step]


def _handle_edit_flow(phone_number: str, state: dict, intent: str, text: str) -> str:
    """Handle the edit event flow (Section 12)."""
    current_step = state["step"]
    events = event_store.get_events_by_host(phone_number)

    if current_step == "select_event":
        # User should reply with a number
        try:
            selection = int(text)
            if 1 <= selection <= len(events):
                selected_event = events[selection - 1]
                state_store.set_selected_event(phone_number, selected_event["id"])
                state_store.set_step(phone_number, "select_field")
                return EDIT_PROMPTS["select_field"]
            else:
                return f"Please enter a number between 1 and {len(events)}."
        except ValueError:
            return f"Please enter a number between 1 and {len(events)}."

    elif current_step == "select_field":
        text_lower = text.lower()

        # Check if user is done editing
        if text_lower == "done":
            event_id = state.get("selected_event_id")
            event = event_store.get_event_by_id(event_id)
            state_store.clear_state(phone_number)
            if event:
                return f"Editing complete!\n\n{format_event_details(event)}"
            return "Editing complete!"

        # User selects a field to edit
        if text in EDIT_FIELDS:
            field = EDIT_FIELDS[text]
            event_id = state.get("selected_event_id")
            event = event_store.get_event_by_id(event_id)
            state_store.set_edit_field(phone_number, field)
            state_store.set_step(phone_number, "new_value")
            display_name = FIELD_DISPLAY_NAMES.get(field, field)

            # Show current value
            current_value = event.get(field, "") if event else ""
            if field == "capacity" and current_value is None:
                current_value = "No limit"

            return f"Currently: {current_value}\n\nEnter the new {display_name}:"
        else:
            return "Please enter a number (1-5) or 'done' to finish editing."

    elif current_step == "new_value":
        event_id = state.get("selected_event_id")
        edit_field = state.get("edit_field")

        if not event_id or not edit_field:
            state_store.clear_state(phone_number)
            return "Something went wrong. Text 'edit event' to try again."

        # Handle capacity specially (try to parse as int)
        value = text
        if edit_field == "capacity":
            if text.lower() in ["none", "no limit", "unlimited"]:
                value = None
            else:
                try:
                    value = int(text)
                except ValueError:
                    value = text

        # Update the event
        success = event_store.update_event(event_id, edit_field, value)
        if success:
            display_name = FIELD_DISPLAY_NAMES.get(edit_field, edit_field)
            state_store.set_step(phone_number, "select_field")
            return f"Updated {display_name}!\n\n{EDIT_PROMPTS['select_field']}"
        else:
            state_store.clear_state(phone_number)
            return "Couldn't update the event. Text 'edit event' to try again."

    return "Text 'cancel' to exit or try again."


def _handle_join_flow(phone_number: str, state: dict, text: str) -> str:
    """Handle the join event flow (Section 18 - Phase 3 request-based joining)."""
    current_step = state["step"]

    if current_step == "select_event":
        # Use discovery function that excludes pending/denied requests
        events = event_store.get_open_events_for_discovery(phone_number)

        if not events:
            state_store.clear_state(phone_number)
            return "No events available to join right now."

        try:
            selection = int(text)
            if 1 <= selection <= len(events):
                selected_event = events[selection - 1]
                event_id = selected_event["id"]
                state_store.clear_state(phone_number)

                # Check if already has pending request
                if event_store.is_request_pending(event_id, phone_number):
                    return "You already requested to join this event. Waiting for host approval."

                # Check if previously denied
                if event_store.is_request_denied(event_id, phone_number):
                    return "Sorry, your request was previously declined."

                # Add pending request
                event_store.add_pending_request(event_id, phone_number)

                # Notify host
                host_phone = selected_event.get("host_phone")
                requester_name = user_store.get_name(phone_number) or phone_number
                event_title = selected_event.get("title")
                host_message = (
                    f"{requester_name} is requesting to join '{event_title}'. "
                    f"Reply 'approve {requester_name}' or 'deny {requester_name}'"
                )
                send_message(host_phone, host_message)

                return "Request sent! Waiting for host approval."
            else:
                return f"Please enter a number between 1 and {len(events)}."
        except ValueError:
            return f"Please enter a number between 1 and {len(events)}."

    return "Text 'cancel' to exit or try again."


def _handle_leave_flow(phone_number: str, state: dict, text: str) -> str:
    """Handle the leave event flow (Section 14)."""
    current_step = state["step"]

    if current_step == "select_event":
        events = event_store.get_joined_events(phone_number)

        if not events:
            state_store.clear_state(phone_number)
            return "You haven't joined any events."

        try:
            selection = int(text)
            if 1 <= selection <= len(events):
                selected_event = events[selection - 1]
                success = event_store.leave_event(selected_event["id"], phone_number)
                state_store.clear_state(phone_number)

                if success:
                    return f"You've left '{selected_event['title']}'. Hope to see you at other events!"
                else:
                    return "Couldn't leave that event. You may not be a participant."
            else:
                return f"Please enter a number between 1 and {len(events)}."
        except ValueError:
            return f"Please enter a number between 1 and {len(events)}."

    return "Text 'cancel' to exit or try again."


def _handle_delete_flow(phone_number: str, state: dict, intent: str, text: str) -> str:
    """Handle the delete event flow (Section 15)."""
    current_step = state["step"]
    events = event_store.get_events_by_host(phone_number)

    if current_step == "select_event":
        if not events:
            state_store.clear_state(phone_number)
            return "You don't have any events to delete."

        try:
            selection = int(text)
            if 1 <= selection <= len(events):
                selected_event = events[selection - 1]
                state_store.set_selected_event(phone_number, selected_event["id"])
                state_store.set_step(phone_number, "confirm_delete")
                return DELETE_PROMPTS["confirm_delete"].format(title=selected_event["title"])
            else:
                return f"Please enter a number between 1 and {len(events)}."
        except ValueError:
            return f"Please enter a number between 1 and {len(events)}."

    elif current_step == "confirm_delete":
        event_id = state.get("selected_event_id")
        text_lower = text.lower()

        if text_lower == "yes" or intent == "confirm":
            # Get event title before deletion
            event = event_store.get_event_by_id(event_id)
            event_title = event["title"] if event else "your event"

            success = event_store.delete_event(event_id)
            state_store.clear_state(phone_number)

            if success:
                return f"'{event_title}' has been deleted."
            else:
                return "Couldn't delete that event. It may have already been removed."
        else:
            state_store.clear_state(phone_number)
            return "Deletion cancelled. Your event is still active."

    return "Text 'cancel' to exit or try again."


# --- Phase 3 Handler Functions ---

def _handle_register_flow(phone_number: str, state: dict, text: str) -> str:
    """Handle the registration flow (Section 17)."""
    current_step = state.get("step")

    if current_step == "get_name":
        name = text.strip()
        if not name:
            return "Please enter your name."

        # Register the user
        user_store.register_user(phone_number, name)

        # Check if there's a pending flow to resume
        pending_flow = state_store.get_pending_flow(phone_number)
        state_store.clear_state(phone_number)

        if pending_flow:
            # Resume the intended flow
            if pending_flow == "create_event":
                state_store.start_flow(phone_number, "create")
                return f"Thanks {name}! You're all set.\n\n{PROMPTS['title']}"
            elif pending_flow == "join_event":
                events = event_store.get_open_events_for_discovery(phone_number)
                if events:
                    state_store.start_flow(phone_number, "join")
                    event_list = format_event_list(events, show_spots=True)
                    return f"Thanks {name}! You're all set.\n\nAvailable events:\n\n{event_list}\n\n{JOIN_PROMPTS['select_event']}"
                return f"Thanks {name}! You're all set. No events available right now. Text 'create event' to host one!"
            elif pending_flow == "edit_event":
                events = event_store.get_events_by_host(phone_number)
                if events:
                    state_store.start_flow(phone_number, "edit")
                    event_list = format_hosted_events(events)
                    return f"Thanks {name}! You're all set.\n\nYour events:\n\n{event_list}\n\n{EDIT_PROMPTS['select_event']}"
                return f"Thanks {name}! You're all set. You haven't created any events yet. Text 'create event' to get started!"
            elif pending_flow == "delete_event":
                events = event_store.get_events_by_host(phone_number)
                if events:
                    state_store.start_flow(phone_number, "delete")
                    event_list = format_hosted_events(events)
                    return f"Thanks {name}! You're all set.\n\nYour events:\n\n{event_list}\n\n{DELETE_PROMPTS['select_event']}"
                return f"Thanks {name}! You're all set. You haven't created any events yet."
            elif pending_flow == "leave_event":
                events = event_store.get_joined_events(phone_number)
                if events:
                    state_store.start_flow(phone_number, "leave")
                    event_list = format_joined_events(events)
                    return f"Thanks {name}! You're all set.\n\nEvents you've joined:\n\n{event_list}\n\n{LEAVE_PROMPTS['select_event']}"
                return f"Thanks {name}! You're all set. You haven't joined any events yet."
            elif pending_flow == "close_event":
                events = [e for e in event_store.get_events_by_host(phone_number)
                          if e.get("status") == "open"]
                if events:
                    state_store.start_flow(phone_number, "close")
                    event_list = format_hosted_events(events)
                    return f"Thanks {name}! You're all set.\n\nYour open events:\n\n{event_list}\n\n{CLOSE_PROMPTS['select_event']}"
                return f"Thanks {name}! You're all set. You don't have any open events."

        return f"Thanks {name}! You're all set. Text 'create event' to get started."

    return "Please enter your name to get started."


def _handle_close_flow(phone_number: str, state: dict, text: str) -> str:
    """Handle the close event flow (Section 19)."""
    current_step = state.get("step")

    # Get host's open events
    events = [e for e in event_store.get_events_by_host(phone_number)
              if e.get("status") == "open"]

    if current_step == "select_event":
        if not events:
            state_store.clear_state(phone_number)
            return "You don't have any open events to close."

        try:
            selection = int(text)
            if 1 <= selection <= len(events):
                selected_event = events[selection - 1]
                state_store.set_selected_event(phone_number, selected_event["id"])
                state_store.set_step(phone_number, "confirm_groupchat")
                return CLOSE_PROMPTS["confirm_groupchat"]
            else:
                return f"Please enter a number between 1 and {len(events)}."
        except ValueError:
            return f"Please enter a number between 1 and {len(events)}."

    elif current_step == "confirm_groupchat":
        event_id = state.get("selected_event_id")
        event = event_store.get_event_by_id(event_id)

        if not event:
            state_store.clear_state(phone_number)
            return "Event not found. Text 'close event' to try again."

        text_lower = text.lower().strip()
        create_chat = text_lower in ["yes", "y"]

        # Close the event
        event_store.close_event(event_id)

        if create_chat:
            # Build group chat with all participants
            host_phone = event.get("host_phone")
            participants = event.get("participants", [])
            all_phones = [host_phone] + participants

            # Get names for all participants
            names_map = user_store.get_all_names(all_phones)
            host_name = names_map.get(host_phone) or "Host"

            # Build attendee list for welcome message with phone numbers
            attendee_lines = [f"- {host_name} ({host_phone}) (Host)"]
            for p_phone in participants:
                p_name = names_map.get(p_phone) or p_phone
                attendee_lines.append(f"- {p_name} ({p_phone})")

            welcome_message = (
                f"Welcome to {event['title']}!\n\n"
                f"When: {event['datetime']}\n"
                f"Where: {event['location']}\n\n"
                f"Attendees:\n"
                + "\n".join(attendee_lines) +
                "\n\nSee you there!"
            )

            # Create group chat
            create_group_chat(all_phones, event["title"], welcome_message)

            state_store.clear_state(phone_number)
            return f"'{event['title']}' is now closed. Group chat created with all participants!"

        state_store.clear_state(phone_number)
        return f"'{event['title']}' is now closed. No group chat was created."

    return "Text 'cancel' to exit or try again."


def _handle_approve(phone_number: str, name: Optional[str]) -> str:
    """Handle host approving a join request (Section 18.2)."""
    if not name:
        return "Please specify a name to approve. Example: 'approve John'"

    # Find pending request matching the name in host's events
    events = event_store.get_events_by_host(phone_number)

    for event in events:
        pending = event.get("pending_requests", [])
        for requester_phone in pending:
            requester_name = user_store.get_name(requester_phone)
            if requester_name and requester_name.lower() == name.lower():
                # Found matching request - approve it
                event_id = event["id"]

                # Remove from pending
                event_store.remove_pending_request(event_id, requester_phone)

                # Add to participants
                event_store.join_event(event_id, requester_phone)

                # Notify requester
                send_message(
                    requester_phone,
                    f"Your request to join '{event['title']}' has been approved! See you there."
                )

                return f"Approved! {requester_name} has been added to '{event['title']}'."

    return f"No pending request found from '{name}'. Check spelling or they may have already been processed."


def _handle_deny(phone_number: str, name: Optional[str]) -> str:
    """Handle host denying a join request (Section 18.2)."""
    if not name:
        return "Please specify a name to deny. Example: 'deny John'"

    # Find pending request matching the name in host's events
    events = event_store.get_events_by_host(phone_number)

    for event in events:
        pending = event.get("pending_requests", [])
        for requester_phone in pending:
            requester_name = user_store.get_name(requester_phone)
            if requester_name and requester_name.lower() == name.lower():
                # Found matching request - deny it
                event_id = event["id"]

                # Remove from pending
                event_store.remove_pending_request(event_id, requester_phone)

                # Add to denied list
                event_store.add_denied_request(event_id, requester_phone)

                # Notify requester
                send_message(
                    requester_phone,
                    f"Your request to join '{event['title']}' was declined."
                )

                return f"Denied. {requester_name}'s request for '{event['title']}' has been declined."

    return f"No pending request found from '{name}'. Check spelling or they may have already been processed."
