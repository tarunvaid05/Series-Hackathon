"""
Supabase Client Module for SEMS (Series Events Messaging System)

Provides a singleton Supabase client for database operations.
Reads SUPABASE_URL and SUPABASE_KEY from environment variables.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Singleton client instance
_client: Optional[Client] = None


def get_client() -> Client:
    """
    Get the singleton Supabase client instance.

    Returns:
        Supabase Client instance

    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY environment variables are not set
    """
    global _client

    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url:
            raise ValueError("SUPABASE_URL environment variable is not set")
        if not key:
            raise ValueError("SUPABASE_KEY environment variable is not set")

        _client = create_client(url, key)

    return _client
