"""
User Store Module for SEMS (Series Events Messaging System)

Manages JSON-based user registration persistence.
Per Project-Requirements.txt Section 17 (User Registration):
- Name stored in data/users.json with phone number as key
- Name persists across all interactions
- First-time users prompted for name, existing users skip
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Path to users JSON file
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")


def _load_users() -> dict:
    """Read users from JSON file, return empty dict if not exists."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_users(users: dict) -> None:
    """Write users to JSON file, create data/ dir if needed."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def is_registered(phone: str) -> bool:
    """Check if phone has name registered."""
    users = _load_users()
    return phone in users and users[phone].get("name") is not None


def get_name(phone: str) -> Optional[str]:
    """Get name for phone, None if not registered."""
    users = _load_users()
    user = users.get(phone)
    if user:
        return user.get("name")
    return None


def register_user(phone: str, name: str) -> bool:
    """Register name for phone, return success."""
    if not phone or not name:
        return False
    users = _load_users()
    users[phone] = {
        "name": name,
        "registered_at": datetime.utcnow().isoformat()
    }
    _save_users(users)
    return True


def get_all_names(phones: List[str]) -> Dict[str, Optional[str]]:
    """Get names for multiple phones (for group chat). Returns dict of phone -> name."""
    users = _load_users()
    result = {}
    for phone in phones:
        user = users.get(phone)
        result[phone] = user.get("name") if user else None
    return result
