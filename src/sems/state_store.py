"""
State Store Module for SEMS (Series Events Messaging System)

Manages in-memory conversation state per user phone number.
Per Project-Requirements.txt Section 3.2, Section 4, Sections 12-15, and Sections 17, 19:
- Maintain conversational state per user phone number until completion or cancellation
- After confirmation, clear state
- Transient in-memory storage only
- Phase 2: Support for create, edit, join, leave, and delete flows
- Phase 3: Support for register and close flows
"""

from typing import Optional, Dict, Any

# In-memory state storage: phone_number -> conversation state
_state: Dict[str, Dict[str, Any]] = {}

# Supported flow types (per Project-Requirements.txt Sections 12-15, 17, 19)
FLOW_TYPES = ["create", "edit", "join", "leave", "delete", "close", "register"]

# Steps for each flow type
STEPS = {
    "create": ["title", "description", "datetime", "location", "capacity", "confirm"],
    "edit": ["select_event", "select_field", "new_value"],
    "join": ["select_event"],
    "leave": ["select_event"],
    "delete": ["select_event", "confirm_delete"],
    "close": ["select_event", "confirm_groupchat"],
    "register": ["get_name"]
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
    return _state.get(phone_number)


def start_flow(phone_number: str, flow_type: str = "create") -> None:
    """Start a new flow for this phone number.
    
    Args:
        phone_number: User's phone number
        flow_type: One of "create", "edit", "join", "leave", "delete"
    """
    if flow_type not in FLOW_TYPES:
        raise ValueError(f"Invalid flow_type: {flow_type}. Must be one of {FLOW_TYPES}")
    
    first_step = STEPS[flow_type][0]
    
    state_data = {
        "step": first_step,
        "flow_type": flow_type,
        "selected_event_id": None,
        "edit_field": None,
        "pending_flow": None  # Stores flow to resume after registration
    }
    
    # Add event data structure only for create flow
    if flow_type == "create":
        state_data["event"] = {
            "phone_number": phone_number,
            "title": None,
            "description": None,
            "datetime": None,
            "location": None,
            "capacity": None
        }
    
    _state[phone_number] = state_data


def update_state(phone_number: str, field: str, value: str) -> None:
    """Update a field in the event data and advance to next step.
    
    This function is primarily for the create flow where we collect event fields.
    For other flows, use set_selected_event() and set_edit_field() helpers.
    """
    if phone_number in _state:
        state = _state[phone_number]
        flow_type = state.get("flow_type", "create")
        
        # For create flow, update the event data
        if flow_type == "create" and "event" in state:
            state["event"][field] = value
        
        # Advance to next step
        current_step = state["step"]
        flow_steps = STEPS[flow_type]
        if current_step in flow_steps:
            current_idx = flow_steps.index(current_step)
            if current_idx < len(flow_steps) - 1:
                state["step"] = flow_steps[current_idx + 1]


def get_event_data(phone_number: str) -> Optional[Dict[str, Any]]:
    """Get the collected event data for a phone number."""
    state = _state.get(phone_number)
    return state["event"] if state else None


def clear_state(phone_number: str) -> None:
    """Clear state for a phone number (on completion or cancel)."""
    _state.pop(phone_number, None)


def set_selected_event(phone_number: str, event_id: str) -> None:
    """Store the selected event ID for edit/join/leave/delete flows."""
    if phone_number in _state:
        _state[phone_number]["selected_event_id"] = event_id


def set_edit_field(phone_number: str, field: str) -> None:
    """Store the field being edited (for edit flow)."""
    if phone_number in _state:
        _state[phone_number]["edit_field"] = field


def get_current_flow_type(phone_number: str) -> Optional[str]:
    """Get the current flow type for a phone number, or None if not in flow."""
    state = _state.get(phone_number)
    return state.get("flow_type") if state else None


def advance_step(phone_number: str) -> None:
    """Manually advance to the next step in the current flow."""
    if phone_number in _state:
        state = _state[phone_number]
        flow_type = state.get("flow_type", "create")
        current_step = state["step"]
        flow_steps = STEPS[flow_type]
        if current_step in flow_steps:
            current_idx = flow_steps.index(current_step)
            if current_idx < len(flow_steps) - 1:
                state["step"] = flow_steps[current_idx + 1]


def set_step(phone_number: str, step: str) -> None:
    """Set the current step explicitly (useful for edit flow looping)."""
    if phone_number in _state:
        _state[phone_number]["step"] = step


def needs_registration(phone: str) -> bool:
    """Check if user is currently in a registration flow.

    Used by intent_handler to check if user needs to complete registration first.
    """
    state = get_state(phone)
    return state is not None and state.get("flow_type") == "register"


def set_pending_flow(phone: str, flow_type: str) -> None:
    """Store the flow the user was trying to start before registration.

    This allows resuming the intended flow after registration completes.
    """
    if phone in _state:
        _state[phone]["pending_flow"] = flow_type


def get_pending_flow(phone: str) -> Optional[str]:
    """Get the pending flow that should resume after registration.

    Returns None if no pending flow or user not in state.
    """
    state = _state.get(phone)
    return state.get("pending_flow") if state else None
