"""
User Store Module for SEMS (Series Events Messaging System)

Manages Supabase-based user registration persistence.
Per Project-Requirements.txt Section 17 (User Registration):
- Name stored in users table with phone number as key
- Name persists across all interactions
- First-time users prompted for name, existing users skip
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sems.supabase_client import get_client

# Simple in-memory cache for user names to reduce Supabase calls
_name_cache: Dict[str, str] = {}


def is_registered(phone: str) -> bool:
    """Check if phone has name registered."""
    try:
        client = get_client()
        response = client.table("users").select("phone, name").eq("phone", phone).maybe_single().execute()
        if response and response.data:
            return response.data.get("name") is not None
        return False
    except Exception as e:
        logging.error(f"Supabase error in is_registered: {e}")
        return False


def get_name(phone: str) -> Optional[str]:
    """Get name for phone, None if not registered. Uses cache to reduce DB calls."""
    # Check cache first
    if phone in _name_cache:
        return _name_cache[phone]

    try:
        client = get_client()
        response = client.table("users").select("name").eq("phone", phone).maybe_single().execute()
        if response and response.data:
            name = response.data.get("name")
            if name:
                _name_cache[phone] = name  # Cache the result
            return name
        return None
    except Exception as e:
        logging.error(f"Supabase error in get_name: {e}")
        return None


def register_user(phone: str, name: str) -> bool:
    """Register name for phone, return success."""
    if not phone or not name:
        return False
    try:
        client = get_client()
        user_data = {
            "phone": phone,
            "name": name,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }
        # Use upsert to handle both insert and update cases
        response = client.table("users").upsert(user_data).execute()
        success = response and response.data is not None and len(response.data) > 0
        if success:
            _name_cache[phone] = name  # Update cache on successful registration
        return success
    except Exception as e:
        logging.error(f"Supabase error in register_user: {e}")
        return False


def get_all_names(phones: List[str]) -> Dict[str, Optional[str]]:
    """Get names for multiple phones (for group chat). Returns dict of phone -> name. Uses cache."""
    if not phones:
        return {}

    result = {}
    uncached_phones = []

    # Check cache first
    for phone in phones:
        if phone in _name_cache:
            result[phone] = _name_cache[phone]
        else:
            uncached_phones.append(phone)
            result[phone] = None  # Default to None

    # Only query for uncached phones
    if uncached_phones:
        try:
            client = get_client()
            response = client.table("users").select("phone, name").in_("phone", uncached_phones).execute()
            if response and response.data:
                for user in response.data:
                    name = user.get("name")
                    phone = user["phone"]
                    result[phone] = name
                    if name:
                        _name_cache[phone] = name  # Update cache
        except Exception as e:
            logging.error(f"Supabase error in get_all_names: {e}")

    return result


def find_users_by_name(name: str) -> List[dict]:
    """
    Find users whose name matches (case-insensitive).

    Args:
        name: The name to search for (partial match supported)

    Returns:
        List of dicts with 'phone' and 'name' keys for matching users
    """
    if not name:
        return []
    try:
        client = get_client()
        # Use ilike for case-insensitive partial matching
        response = client.table("users").select("phone, name").ilike("name", f"%{name}%").execute()
        if response and response.data:
            return [{"phone": u["phone"], "name": u["name"]} for u in response.data]
        return []
    except Exception as e:
        logging.error(f"Supabase error in find_users_by_name: {e}")
        return []


def get_user(phone: str) -> Optional[dict]:
    """
    Get full user object for a phone number.

    Args:
        phone: The phone number to look up

    Returns:
        Full user dict with all fields (name, registered_at, bio, image, age)
        or None if user not found.

    Schema:
        {
            "name": str,           # required
            "registered_at": str,  # required (ISO timestamp)
            "bio": str,            # optional
            "image": str,          # optional (base64 encoded)
            "age": int             # optional
        }
    """
    try:
        client = get_client()
        response = client.table("users").select("*").eq("phone", phone).maybe_single().execute()
        if response and response.data:
            # Return without the phone key to match original format
            user = response.data.copy()
            user.pop("phone", None)
            return user
        return None
    except Exception as e:
        logging.error(f"Supabase error in get_user: {e}")
        return None


def update_user(phone: str, updates: dict) -> bool:
    """
    Update specific fields for an existing user.

    Args:
        phone: The phone number of the user to update
        updates: Dict of fields to update (bio, image, age, etc.)

    Returns:
        True if user exists and was updated, False if user not found.

    Note:
        - Only updates provided fields, preserves existing data
        - Cannot update 'name' or 'registered_at' through this function
          for safety (use register_user for initial registration)
    """
    if not phone or not updates:
        return False

    try:
        # First check if user exists
        client = get_client()
        check = client.table("users").select("phone").eq("phone", phone).maybe_single().execute()
        if not check or not check.data:
            return False

        # Update the user
        response = client.table("users").update(updates).eq("phone", phone).execute()
        return response and response.data is not None and len(response.data) > 0
    except Exception as e:
        logging.error(f"Supabase error in update_user: {e}")
        return False
