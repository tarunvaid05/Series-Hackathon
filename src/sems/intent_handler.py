"""Intent detection and conversational flow logic for SEMS."""

from typing import List

from sems import state_store, event_store

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

# Prompts for create flow steps
PROMPTS = {
    "title": "What's the title of your event?",
    "description": "Got it! Now give me a brief description of the event.",
    "datetime": "When is this event? (date and time)",
    "location": "Where will it be held?",
    "capacity": "How many people can attend? (or say 'skip' for no limit)",
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


def detect_intent(text: str) -> str:
    """
    Detect the intent from user message.
    Returns: "create_event", "edit_event", "join_event", "leave_event", "delete_event",
             "cancel", "restart", "confirm", "skip", or "input"

    IMPORTANT: Check longer phrases first to avoid conflicts.
    DELETE_INTENTS checked before CANCEL_KEYWORDS to prevent "delete event" matching "cancel".
    """
    text_lower = text.lower().strip()

    # Check for restart first
    for keyword in RESTART_KEYWORDS:
        if keyword in text_lower:
            return "restart"

    # Check DELETE_INTENTS before cancel to avoid "delete event" matching "cancel"
    for phrase in DELETE_INTENTS:
        if phrase in text_lower:
            return "delete_event"

    # Check for cancel (can happen anytime)
    for keyword in CANCEL_KEYWORDS:
        if keyword in text_lower:
            return "cancel"

    # Check for create event intent
    for phrase in CREATE_INTENTS:
        if phrase in text_lower:
            return "create_event"

    # Check for edit event intent
    for phrase in EDIT_INTENTS:
        if phrase in text_lower:
            return "edit_event"

    # Check for join/discover event intent
    for phrase in JOIN_INTENTS:
        if phrase in text_lower:
            return "join_event"

    # Check for leave event intent
    for phrase in LEAVE_INTENTS:
        if phrase in text_lower:
            return "leave_event"

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

    This is the main flow logic per Project-Requirements.txt Sections 3, 5, and 12-16.
    Handles create, edit, join, leave, and delete flows.
    """
    intent = detect_intent(text)
    state = state_store.get_state(phone_number)
    text_stripped = text.strip()

    # Handle cancel - always works (clears any flow)
    if intent == "cancel":
        state_store.clear_state(phone_number)
        return "Cancelled. Text 'create event' to make a new event, or 'find events' to see what's happening."

    # Handle restart - clears state and starts create flow
    if intent == "restart":
        state_store.clear_state(phone_number)
        state_store.start_flow(phone_number, "create")
        return PROMPTS["title"]

    # --- NOT IN A FLOW: Check for intent to start a new flow ---
    if state is None:
        return _handle_new_intent(phone_number, intent)

    # --- IN A FLOW: Route to appropriate flow handler ---
    flow_type = state.get("flow_type", "create")

    if flow_type == "create":
        return _handle_create_flow(phone_number, state, intent, text_stripped)
    elif flow_type == "edit":
        return _handle_edit_flow(phone_number, state, intent, text_stripped)
    elif flow_type == "join":
        return _handle_join_flow(phone_number, state, text_stripped)
    elif flow_type == "leave":
        return _handle_leave_flow(phone_number, state, text_stripped)
    elif flow_type == "delete":
        return _handle_delete_flow(phone_number, state, intent, text_stripped)
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
        events = event_store.get_joinable_events(phone_number)
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

    else:
        # Default welcome message
        return ("Hi! Here's what you can do:\n"
                "- 'create event' to host a new event\n"
                "- 'find events' to see what's happening\n"
                "- 'edit event' to modify your events\n"
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
            state_store.set_edit_field(phone_number, field)
            state_store.set_step(phone_number, "new_value")
            display_name = FIELD_DISPLAY_NAMES.get(field, field)
            return EDIT_PROMPTS["new_value"].format(field=display_name)
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
    """Handle the join event flow (Section 13)."""
    current_step = state["step"]

    if current_step == "select_event":
        events = event_store.get_joinable_events(phone_number)

        if not events:
            state_store.clear_state(phone_number)
            return "No events available to join right now."

        try:
            selection = int(text)
            if 1 <= selection <= len(events):
                selected_event = events[selection - 1]
                success = event_store.join_event(selected_event["id"], phone_number)
                state_store.clear_state(phone_number)

                if success:
                    # Get updated event to show spots
                    updated_event = event_store.get_event_by_id(selected_event["id"])
                    participants = updated_event.get("participants", [])
                    capacity = updated_event.get("capacity")

                    if capacity:
                        spots_info = f" ({len(participants)}/{capacity} spots filled)"
                    else:
                        spots_info = ""

                    return f"You're in! You've joined '{selected_event['title']}'{spots_info}. See you there!"
                else:
                    return "Couldn't join that event. It may be full or you may already be signed up."
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
