-- SEMS Supabase Schema
-- Series Events Messaging System Database Schema
-- Version: 1.0.0

-- =============================================================================
-- USERS TABLE
-- Per Project-Requirements.txt Section 17 (User Registration)
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    phone TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    bio TEXT,
    image TEXT,
    age INTEGER
);

-- Index for name searching (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_users_name_lower ON users (LOWER(name));

-- =============================================================================
-- EVENTS TABLE
-- Per Project-Requirements.txt Section 11 (Data Persistence)
-- Note: NO foreign key on host_phone to allow unregistered hosts
-- =============================================================================
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    host_phone TEXT NOT NULL,  -- NO foreign key constraint
    title TEXT NOT NULL,
    description TEXT,
    datetime TEXT,
    location TEXT,
    capacity INTEGER,
    participants TEXT[] DEFAULT '{}',
    status TEXT DEFAULT 'open',
    pending_requests TEXT[] DEFAULT '{}',
    denied_requests TEXT[] DEFAULT '{}',
    private BOOLEAN DEFAULT false,
    invited_phones TEXT[] DEFAULT '{}',
    pending_invites TEXT[] DEFAULT '{}',
    group_chat_id INTEGER,
    simulated_days INTEGER DEFAULT 0
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_events_host_phone ON events (host_phone);
CREATE INDEX IF NOT EXISTS idx_events_status ON events (status);
CREATE INDEX IF NOT EXISTS idx_events_group_chat_id ON events (group_chat_id);

-- =============================================================================
-- CONVERSATION_STATE TABLE
-- Per Project-Requirements.txt Section 3.2 (Messaging behavior)
-- Replaces in-memory _state dict
-- =============================================================================
CREATE TABLE IF NOT EXISTS conversation_state (
    phone_number TEXT PRIMARY KEY,
    step TEXT NOT NULL,
    flow_type TEXT NOT NULL,
    selected_event_id UUID,
    edit_field TEXT,
    pending_flow TEXT,
    event_data JSONB,  -- For create flow collected fields
    search_results JSONB,  -- For invite flow
    selected_user_phone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for flow type queries
CREATE INDEX IF NOT EXISTS idx_conversation_state_flow_type ON conversation_state (flow_type);

-- =============================================================================
-- TRIGGER: Auto-update updated_at on conversation_state changes
-- =============================================================================
CREATE OR REPLACE FUNCTION update_conversation_state_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_conversation_state_updated_at ON conversation_state;
CREATE TRIGGER trigger_conversation_state_updated_at
    BEFORE UPDATE ON conversation_state
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_state_updated_at();
