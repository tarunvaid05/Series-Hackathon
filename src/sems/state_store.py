"""
State Store Module for SEMS (Series Events Messaging System)

Manages in-memory conversation state per user phone number.
Per Project-Requirements.txt Section 3.2 and Section 4:
- Maintain conversational state per user phone number until completion or cancellation
- After confirmation, clear state
- Transient in-memory storage only
"""

from typing import Optional, Dict, Any

# In-memory state storage: phone_number -> conversation state
_state: Dict[str, Dict[str, Any]] = {}

# Event creation flow steps
STEPS = ["title", "description", "datetime", "location", "capacity", "confirm"]


def get_state(phone_number: str) -> Optional[Dict[str, Any]]:
    """Get conversation state for a phone number, or None if not in flow."""
    return _state.get(phone_number)


def start_flow(phone_number: str) -> None:
    """Start a new event creation flow for this phone number."""
    _state[phone_number] = {
        "step": "title",  # Current step in flow
        "event": {        # Collected event data
            "phone_number": phone_number,
            "title": None,
            "description": None,
            "datetime": None,
            "location": None,
            "capacity": None
        }
    }


def update_state(phone_number: str, field: str, value: str) -> None:
    """Update a field in the event data and advance to next step."""
    if phone_number in _state:
        _state[phone_number]["event"][field] = value
        current_step = _state[phone_number]["step"]
        current_idx = STEPS.index(current_step)
        if current_idx < len(STEPS) - 1:
            _state[phone_number]["step"] = STEPS[current_idx + 1]


def get_event_data(phone_number: str) -> Optional[Dict[str, Any]]:
    """Get the collected event data for a phone number."""
    state = _state.get(phone_number)
    return state["event"] if state else None


def clear_state(phone_number: str) -> None:
    """Clear state for a phone number (on completion or cancel)."""
    _state.pop(phone_number, None)
