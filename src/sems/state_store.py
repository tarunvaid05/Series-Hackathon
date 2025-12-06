"""
State Store Module for SEMS (Series Events Messaging System)

Manages Supabase-based conversation state per user phone number.
Per Project-Requirements.txt Section 3.2, Section 4, Sections 12-15, and Sections 17, 19:
- Maintain conversational state per user phone number until completion or cancellation
- After confirmation, clear state
- Phase 2: Support for create, edit, join, leave, and delete flows
- Phase 3: Support for register and close flows
"""

import logging
from typing import Optional, Dict, Any

from sems.supabase_client import get_client

# Supported flow types (per Project-Requirements.txt Sections 12-15, 17, 19)
FLOW_TYPES = ["create", "edit", "join", "leave", "delete", "close", "register", "invite", "view_attendees"]

# Steps for each flow type
STEPS = {
    "create": ["title", "description", "datetime", "location", "capacity", "private", "confirm"],
    "edit": ["select_event", "select_field", "new_value"],
    "join": ["select_event"],
    "leave": ["select_event"],
    "delete": ["select_event", "confirm_delete"],
    "close": ["select_event", "confirm_groupchat"],
    "register": ["get_name"],
    "invite": ["select_event", "search_user", "select_user"],
    "view_attendees": ["select_event"]
}


def get_state(phone_number: str) -> Optional[Dict[str, Any]]:
    """Get conversation state for a phone number, or None if not in flow.

    Returns state dict including:
    - step: Current step in flow
    - flow_type: Which flow type (create, edit, join, leave, delete)
    - event: Collected event data (for create flow)
    - selected_event_id: Selected event ID (for edit/join/leave/delete flows)
    - edit_field: Field being edited (for edit flow)
    """
    try:
        client = get_client()
        response = client.table("conversation_state").select("*").eq("phone_number", phone_number).maybe_single().execute()

        if not response or not response.data:
            return None

        data = response.data
        state = {
            "step": data.get("step"),
            "flow_type": data.get("flow_type"),
            "selected_event_id": data.get("selected_event_id"),
            "edit_field": data.get("edit_field"),
            "pending_flow": data.get("pending_flow"),
        }

        # Add event data for create flow
        if data.get("event_data"):
            state["event"] = data["event_data"]

        # Add search results for invite flow
        if data.get("search_results"):
            state["search_results"] = data["search_results"]

        if data.get("selected_user_phone"):
            state["selected_user_phone"] = data["selected_user_phone"]

        return state
    except Exception as e:
        logging.error(f"Supabase error in get_state: {e}")
        return None


def start_flow(phone_number: str, flow_type: str = "create") -> bool:
    """Start a new flow for this phone number.

    Args:
        phone_number: User's phone number
        flow_type: One of "create", "edit", "join", "leave", "delete"

    Returns:
        True if successful, False otherwise
    """
    if flow_type not in FLOW_TYPES:
        logging.error(f"Invalid flow_type: {flow_type}. Must be one of {FLOW_TYPES}")
        return False

    first_step = STEPS[flow_type][0]

    state_data = {
        "phone_number": phone_number,
        "step": first_step,
        "flow_type": flow_type,
        "selected_event_id": None,
        "edit_field": None,
        "pending_flow": None,
        "event_data": None,
        "search_results": None,
        "selected_user_phone": None
    }

    # Add event data structure only for create flow
    if flow_type == "create":
        state_data["event_data"] = {
            "phone_number": phone_number,
            "title": None,
            "description": None,
            "datetime": None,
            "location": None,
            "capacity": None,
            "private": None
        }

    try:
        client = get_client()
        # Use upsert to handle both new and existing states
        response = client.table("conversation_state").upsert(state_data).execute()
        return response and response.data is not None and len(response.data) > 0
    except Exception as e:
        logging.error(f"Supabase error in start_flow: {e}")
        return False


def update_state(phone_number: str, field: str, value: str) -> bool:
    """Update a field in the event data and advance to next step.

    This function is primarily for the create flow where we collect event fields.
    For other flows, use set_selected_event() and set_edit_field() helpers.

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        response = client.table("conversation_state").select("*").eq("phone_number", phone_number).maybe_single().execute()

        if not response or not response.data:
            return False

        data = response.data
        flow_type = data.get("flow_type", "create")
        current_step = data.get("step")

        updates = {}

        # For create flow, update the event data
        if flow_type == "create":
            event_data = data.get("event_data") or {}
            event_data[field] = value
            updates["event_data"] = event_data

        # Advance to next step
        flow_steps = STEPS.get(flow_type, [])
        if current_step in flow_steps:
            current_idx = flow_steps.index(current_step)
            if current_idx < len(flow_steps) - 1:
                updates["step"] = flow_steps[current_idx + 1]

        if updates:
            update_response = client.table("conversation_state").update(updates).eq("phone_number", phone_number).execute()
            return update_response and update_response.data is not None and len(update_response.data) > 0
        return True
    except Exception as e:
        logging.error(f"Supabase error in update_state: {e}")
        return False


def get_event_data(phone_number: str) -> Optional[Dict[str, Any]]:
    """Get the collected event data for a phone number."""
    try:
        client = get_client()
        response = client.table("conversation_state").select("event_data").eq("phone_number", phone_number).maybe_single().execute()

        if response and response.data:
            return response.data.get("event_data")
        return None
    except Exception as e:
        logging.error(f"Supabase error in get_event_data: {e}")
        return None


def clear_state(phone_number: str) -> bool:
    """Clear state for a phone number (on completion or cancel).

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        response = client.table("conversation_state").delete().eq("phone_number", phone_number).execute()
        return response is not None
    except Exception as e:
        logging.error(f"Supabase error in clear_state: {e}")
        return False


def set_selected_event(phone_number: str, event_id: str) -> bool:
    """Store the selected event ID for edit/join/leave/delete flows.

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        response = client.table("conversation_state").update({"selected_event_id": event_id}).eq("phone_number", phone_number).execute()
        return response and response.data is not None and len(response.data) > 0
    except Exception as e:
        logging.error(f"Supabase error in set_selected_event: {e}")
        return False


def set_edit_field(phone_number: str, field: str) -> bool:
    """Store the field being edited (for edit flow).

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        response = client.table("conversation_state").update({"edit_field": field}).eq("phone_number", phone_number).execute()
        return response and response.data is not None and len(response.data) > 0
    except Exception as e:
        logging.error(f"Supabase error in set_edit_field: {e}")
        return False


def get_current_flow_type(phone_number: str) -> Optional[str]:
    """Get the current flow type for a phone number, or None if not in flow."""
    try:
        client = get_client()
        response = client.table("conversation_state").select("flow_type").eq("phone_number", phone_number).maybe_single().execute()

        if response and response.data:
            return response.data.get("flow_type")
        return None
    except Exception as e:
        logging.error(f"Supabase error in get_current_flow_type: {e}")
        return None


def advance_step(phone_number: str) -> bool:
    """Manually advance to the next step in the current flow.

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        response = client.table("conversation_state").select("step, flow_type").eq("phone_number", phone_number).maybe_single().execute()

        if not response or not response.data:
            return False

        flow_type = response.data.get("flow_type", "create")
        current_step = response.data.get("step")
        flow_steps = STEPS.get(flow_type, [])

        if current_step in flow_steps:
            current_idx = flow_steps.index(current_step)
            if current_idx < len(flow_steps) - 1:
                new_step = flow_steps[current_idx + 1]
                update_response = client.table("conversation_state").update({"step": new_step}).eq("phone_number", phone_number).execute()
                return update_response and update_response.data is not None and len(update_response.data) > 0
        return True
    except Exception as e:
        logging.error(f"Supabase error in advance_step: {e}")
        return False


def set_step(phone_number: str, step: str) -> bool:
    """Set the current step explicitly (useful for edit flow looping).

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        response = client.table("conversation_state").update({"step": step}).eq("phone_number", phone_number).execute()
        return response and response.data is not None and len(response.data) > 0
    except Exception as e:
        logging.error(f"Supabase error in set_step: {e}")
        return False


def needs_registration(phone: str) -> bool:
    """Check if user is currently in a registration flow.

    Used by intent_handler to check if user needs to complete registration first.
    """
    state = get_state(phone)
    return state is not None and state.get("flow_type") == "register"


def set_pending_flow(phone: str, flow_type: str) -> bool:
    """Store the flow the user was trying to start before registration.

    This allows resuming the intended flow after registration completes.

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        response = client.table("conversation_state").update({"pending_flow": flow_type}).eq("phone_number", phone).execute()
        return response and response.data is not None and len(response.data) > 0
    except Exception as e:
        logging.error(f"Supabase error in set_pending_flow: {e}")
        return False


def get_pending_flow(phone: str) -> Optional[str]:
    """Get the pending flow that should resume after registration.

    Returns None if no pending flow or user not in state.
    """
    try:
        client = get_client()
        response = client.table("conversation_state").select("pending_flow").eq("phone_number", phone).maybe_single().execute()

        if response and response.data:
            return response.data.get("pending_flow")
        return None
    except Exception as e:
        logging.error(f"Supabase error in get_pending_flow: {e}")
        return None


def start_invite_flow(phone_number: str) -> dict:
    """Initialize invite flow state.

    The invite flow allows users to invite others to their events:
    1. select_event - User selects which event to invite someone to
    2. search_user - User provides a name to search for
    3. select_user - User selects from search results (if multiple matches)

    Returns:
        The initialized state dict for the invite flow, or empty dict on error.
    """
    try:
        if not start_flow(phone_number, "invite"):
            return {}

        client = get_client()
        client.table("conversation_state").update({
            "selected_event_id": None,
            "search_results": [],
            "selected_user_phone": None
        }).eq("phone_number", phone_number).execute()

        return get_state(phone_number) or {}
    except Exception as e:
        logging.error(f"Supabase error in start_invite_flow: {e}")
        return {}
