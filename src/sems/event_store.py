"""
Event Store Module for SEMS (Series Events Messaging System)

Manages JSON-based event persistence.
Per Project-Requirements.txt Section 11 (Data Persistence):
- Local JSON file storage at data/events.json
- Events persisted on creation confirmation
- Updates saved immediately on edit confirmation
- File read on startup and written on each modification
"""

import json
import os
import uuid
from typing import Any, List, Optional

# Path to events JSON file
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")


def _load_events() -> List[dict]:
    """Read events from JSON file, return empty list if not exists."""
    if not os.path.exists(EVENTS_FILE):
        return []
    try:
        with open(EVENTS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_events(events: List[dict]) -> None:
    """Write events to JSON file, create data/ dir if needed."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    with open(EVENTS_FILE, "w") as f:
        json.dump(events, f, indent=2)


def create_event(event_data: dict) -> dict:
    """Add UUID, empty participants list, Phase 3 fields, save, return event."""
    events = _load_events()
    event = {
        "id": str(uuid.uuid4()),
        "host_phone": event_data.get("host_phone") or event_data.get("phone_number"),
        "title": event_data.get("title"),
        "description": event_data.get("description"),
        "datetime": event_data.get("datetime"),
        "location": event_data.get("location"),
        "capacity": event_data.get("capacity"),
        "participants": [],
        "status": "open",
        "pending_requests": [],
        "denied_requests": [],
        "private": event_data.get("private", False),
        "invited_phones": [],
        "pending_invites": []
    }
    events.append(event)
    _save_events(events)
    return event


def get_events_by_host(phone: str) -> List[dict]:
    """Filter events by host_phone."""
    events = _load_events()
    return [e for e in events if e.get("host_phone") == phone]


def get_joinable_events(phone: str) -> List[dict]:
    """Get events user can join: exclude own, full, joined, closed, denied."""
    events = _load_events()
    joinable = []
    for event in events:
        # Exclude own events
        if event.get("host_phone") == phone:
            continue
        # Exclude closed events (Phase 3)
        if event.get("status") != "open":
            continue
        # Exclude already joined
        if phone in event.get("participants", []):
            continue
        # Exclude denied requests (Phase 3)
        if phone in event.get("denied_requests", []):
            continue
        # Exclude full capacity events
        capacity = event.get("capacity")
        if capacity is not None:
            try:
                capacity_int = int(capacity)
                current_count = len(event.get("participants", []))
                if current_count >= capacity_int:
                    continue
            except (ValueError, TypeError):
                pass  # Invalid capacity, treat as unlimited
        joinable.append(event)
    return joinable


def get_joined_events(phone: str) -> List[dict]:
    """Get events where phone is in participants."""
    events = _load_events()
    return [e for e in events if phone in e.get("participants", [])]


def get_event_by_id(event_id: str) -> Optional[dict]:
    """Find event by id."""
    events = _load_events()
    for event in events:
        if event.get("id") == event_id:
            return event
    return None


def update_event(event_id: str, field: str, value: Any) -> bool:
    """Update event field, save, return success."""
    events = _load_events()
    for event in events:
        if event.get("id") == event_id:
            event[field] = value
            _save_events(events)
            return True
    return False


def delete_event(event_id: str) -> bool:
    """Remove event, save, return success."""
    events = _load_events()
    for i, event in enumerate(events):
        if event.get("id") == event_id:
            events.pop(i)
            _save_events(events)
            return True
    return False


def join_event(event_id: str, phone: str) -> bool:
    """Add to participants if allowed, save."""
    events = _load_events()
    for event in events:
        if event.get("id") == event_id:
            # Cannot join own event
            if event.get("host_phone") == phone:
                return False
            # Cannot join if already joined
            participants = event.get("participants", [])
            if phone in participants:
                return False
            # Cannot join if at capacity
            capacity = event.get("capacity")
            if capacity is not None:
                try:
                    capacity_int = int(capacity)
                    if len(participants) >= capacity_int:
                        return False
                except (ValueError, TypeError):
                    pass  # Invalid capacity, treat as unlimited
            # Add participant
            participants.append(phone)
            event["participants"] = participants
            _save_events(events)
            return True
    return False


def leave_event(event_id: str, phone: str) -> bool:
    """Remove from participants, save."""
    events = _load_events()
    for event in events:
        if event.get("id") == event_id:
            participants = event.get("participants", [])
            if phone in participants:
                participants.remove(phone)
                event["participants"] = participants
                _save_events(events)
                return True
            return False
    return False


def add_pending_request(event_id: str, phone: str) -> bool:
    """Add phone to pending_requests list for event."""
    events = _load_events()
    for event in events:
        if event.get("id") == event_id:
            pending = event.get("pending_requests", [])
            if phone not in pending:
                pending.append(phone)
                event["pending_requests"] = pending
                _save_events(events)
                return True
            return False
    return False


def remove_pending_request(event_id: str, phone: str) -> bool:
    """Remove phone from pending_requests list for event."""
    events = _load_events()
    for event in events:
        if event.get("id") == event_id:
            pending = event.get("pending_requests", [])
            if phone in pending:
                pending.remove(phone)
                event["pending_requests"] = pending
                _save_events(events)
                return True
            return False
    return False


def add_denied_request(event_id: str, phone: str) -> bool:
    """Add phone to denied_requests list for event."""
    events = _load_events()
    for event in events:
        if event.get("id") == event_id:
            denied = event.get("denied_requests", [])
            if phone not in denied:
                denied.append(phone)
                event["denied_requests"] = denied
                _save_events(events)
                return True
            return False
    return False


def is_request_pending(event_id: str, phone: str) -> bool:
    """Check if phone has a pending request for event."""
    event = get_event_by_id(event_id)
    if event:
        return phone in event.get("pending_requests", [])
    return False


def is_request_denied(event_id: str, phone: str) -> bool:
    """Check if phone was denied for event."""
    event = get_event_by_id(event_id)
    if event:
        return phone in event.get("denied_requests", [])
    return False


def close_event(event_id: str) -> bool:
    """Set event status to closed."""
    return update_event(event_id, "status", "closed")


def get_open_events_for_discovery(phone: str) -> List[dict]:
    """Get events for discovery: open, not own, not full, not joined, not denied, not private (unless invited)."""
    events = _load_events()
    discoverable = []
    for event in events:
        # Must be open status
        if event.get("status") != "open":
            continue
        # Exclude own events
        if event.get("host_phone") == phone:
            continue
        # Exclude already joined
        if phone in event.get("participants", []):
            continue
        # Exclude denied requests
        if phone in event.get("denied_requests", []):
            continue
        # Exclude full capacity events
        capacity = event.get("capacity")
        if capacity is not None:
            try:
                capacity_int = int(capacity)
                current_count = len(event.get("participants", []))
                if current_count >= capacity_int:
                    continue
            except (ValueError, TypeError):
                pass  # Invalid capacity, treat as unlimited
        # Exclude private events unless user is invited
        if event.get("private", False):
            invited = event.get("invited_phones", [])
            pending = event.get("pending_invites", [])
            if phone not in invited and phone not in pending:
                continue
        discoverable.append(event)
    return discoverable


def set_group_chat_id(event_id: str, chat_id: int) -> bool:
    """Set the group_chat_id for an event.

    Args:
        event_id: The event's unique ID
        chat_id: The chat ID from the messaging API

    Returns:
        True if successful, False otherwise
    """
    return update_event(event_id, "group_chat_id", chat_id)


def get_event_by_group_chat_id(chat_id: int) -> Optional[dict]:
    """Find an event by its group_chat_id.

    When multiple events share the same group_chat_id (due to API reusing
    existing chats with same participants), returns the most recently
    closed event.

    Args:
        chat_id: The group chat ID to search for

    Returns:
        The event dict if found, None otherwise
    """
    events = _load_events()
    matching_events = [e for e in events if e.get("group_chat_id") == chat_id]
    
    if not matching_events:
        return None
    
    if len(matching_events) == 1:
        return matching_events[0]
    
    # Multiple events share this chat_id - return the most recently closed one
    # Events are appended in order, so last one is most recent
    return matching_events[-1]


def get_simulated_days(event_id: str) -> int:
    """Get the cumulative simulated days passed for an event.
    
    Args:
        event_id: The event's unique ID
        
    Returns:
        Number of simulated days passed, defaults to 0
    """
    event = get_event_by_id(event_id)
    if event:
        return event.get("simulated_days", 0)
    return 0


def add_simulated_days(event_id: str, days: int) -> int:
    """Add days to the simulated time for an event.
    
    Args:
        event_id: The event's unique ID
        days: Number of days to add
        
    Returns:
        New total simulated days
    """
    events = _load_events()
    for event in events:
        if event.get("id") == event_id:
            current = event.get("simulated_days", 0)
            new_total = current + days
            event["simulated_days"] = new_total
            _save_events(events)
            return new_total
    return 0


def reset_simulated_time(event_id: str) -> bool:
    """Reset simulated time for an event back to 0.

    Args:
        event_id: The event's unique ID

    Returns:
        True if successful, False otherwise
    """
    return update_event(event_id, "simulated_days", 0)


def add_invite(event_id: str, phone: str) -> bool:
    """Add phone to pending_invites list if not already there and not a participant.

    Args:
        event_id: The event's unique ID
        phone: Phone number to invite

    Returns:
        True on success, False if already invited or participant
    """
    events = _load_events()
    for event in events:
        if event.get("id") == event_id:
            # Check if already a participant
            if phone in event.get("participants", []):
                return False
            # Check if already has pending invite
            pending_invites = event.get("pending_invites", [])
            if phone in pending_invites:
                return False
            # Check if already in invited_phones (accepted previously)
            if phone in event.get("invited_phones", []):
                return False
            # Add to pending invites
            pending_invites.append(phone)
            event["pending_invites"] = pending_invites
            _save_events(events)
            return True
    return False


def get_pending_invites(event_id: str) -> List[str]:
    """Return list of pending invite phone numbers for the event.

    Args:
        event_id: The event's unique ID

    Returns:
        List of phone numbers with pending invites
    """
    event = get_event_by_id(event_id)
    if event:
        return event.get("pending_invites", [])
    return []


def accept_invite(event_id: str, phone: str) -> bool:
    """Accept an invite: remove from pending_invites, add to participants and invited_phones.

    Args:
        event_id: The event's unique ID
        phone: Phone number accepting the invite

    Returns:
        True on success, False if no pending invite
    """
    events = _load_events()
    for event in events:
        if event.get("id") == event_id:
            pending_invites = event.get("pending_invites", [])
            if phone not in pending_invites:
                return False
            # Remove from pending_invites
            pending_invites.remove(phone)
            event["pending_invites"] = pending_invites
            # Add to participants
            participants = event.get("participants", [])
            if phone not in participants:
                participants.append(phone)
                event["participants"] = participants
            # Add to invited_phones for tracking
            invited_phones = event.get("invited_phones", [])
            if phone not in invited_phones:
                invited_phones.append(phone)
                event["invited_phones"] = invited_phones
            _save_events(events)
            return True
    return False


def decline_invite(event_id: str, phone: str) -> bool:
    """Decline an invite: remove from pending_invites.

    Args:
        event_id: The event's unique ID
        phone: Phone number declining the invite

    Returns:
        True on success, False if no pending invite
    """
    events = _load_events()
    for event in events:
        if event.get("id") == event_id:
            pending_invites = event.get("pending_invites", [])
            if phone in pending_invites:
                pending_invites.remove(phone)
                event["pending_invites"] = pending_invites
                _save_events(events)
                return True
            return False
    return False


def is_invited(event_id: str, phone: str) -> bool:
    """Check if phone is in invited_phones or pending_invites.

    Args:
        event_id: The event's unique ID
        phone: Phone number to check

    Returns:
        True if phone is invited (pending or accepted)
    """
    event = get_event_by_id(event_id)
    if event:
        return (phone in event.get("invited_phones", []) or
                phone in event.get("pending_invites", []))
    return False


def has_pending_invite(event_id: str, phone: str) -> bool:
    """Check if phone has a pending invite for the event.

    Args:
        event_id: The event's unique ID
        phone: Phone number to check

    Returns:
        True if phone has a pending invite
    """
    event = get_event_by_id(event_id)
    if event:
        return phone in event.get("pending_invites", [])
    return False


def get_all_events() -> List[dict]:
    """Return all events.

    Returns:
        List of all event dictionaries
    """
    return _load_events()
