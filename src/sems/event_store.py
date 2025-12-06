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
    """Add UUID, empty participants list, save, return event."""
    events = _load_events()
    event = {
        "id": str(uuid.uuid4()),
        "host_phone": event_data.get("host_phone") or event_data.get("phone_number"),
        "title": event_data.get("title"),
        "description": event_data.get("description"),
        "datetime": event_data.get("datetime"),
        "location": event_data.get("location"),
        "capacity": event_data.get("capacity"),
        "participants": []
    }
    events.append(event)
    _save_events(events)
    return event


def get_events_by_host(phone: str) -> List[dict]:
    """Filter events by host_phone."""
    events = _load_events()
    return [e for e in events if e.get("host_phone") == phone]


def get_joinable_events(phone: str) -> List[dict]:
    """Get events user can join: exclude own events, full capacity, already joined."""
    events = _load_events()
    joinable = []
    for event in events:
        # Exclude own events
        if event.get("host_phone") == phone:
            continue
        # Exclude already joined
        if phone in event.get("participants", []):
            continue
        # Exclude full capacity events
        capacity = event.get("capacity")
        if capacity is not None:
            current_count = len(event.get("participants", []))
            if current_count >= capacity:
                continue
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
            if capacity is not None and len(participants) >= capacity:
                return False
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
