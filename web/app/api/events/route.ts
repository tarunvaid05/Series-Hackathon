import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

interface Event {
  id: string;
  host_phone: string;
  title: string;
  description: string;
  datetime: string;
  location: string;
  capacity: number | null;
  participants: string[];
  status: 'open' | 'closed';
  pending_requests: string[];
  denied_requests: string[];
  private?: boolean;
  invited_phones?: string[];
  pending_invites?: string[];
  group_chat_id?: number;
  simulated_days?: number;
}

// GET /api/events - Return all events (optionally filter by query params)
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);

    let query = supabase.from('events').select('*');

    // Filter by host_phone if provided
    const hostPhone = searchParams.get('host_phone');
    if (hostPhone) {
      query = query.eq('host_phone', hostPhone);
    }

    // Filter by status if provided
    const status = searchParams.get('status');
    if (status === 'open' || status === 'closed') {
      query = query.eq('status', status);
    }

    // Filter by participant phone if provided
    const participant = searchParams.get('participant');
    if (participant) {
      query = query.contains('participants', [participant]);
    }

    const { data: events, error } = await query;

    if (error) {
      console.error('Supabase error reading events:', error);
      return NextResponse.json({ error: 'Failed to read events' }, { status: 500 });
    }

    return NextResponse.json(events || []);
  } catch (error) {
    console.error('Error reading events:', error);
    return NextResponse.json({ error: 'Failed to read events' }, { status: 500 });
  }
}

// POST /api/events - Create a new event
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validate required fields
    const { host_phone, title, description, datetime, location, capacity } = body;

    if (!host_phone || !title || !description || !datetime || !location) {
      return NextResponse.json(
        { error: 'Missing required fields: host_phone, title, description, datetime, location' },
        { status: 400 }
      );
    }

    const newEvent: Omit<Event, 'id'> = {
      host_phone,
      title,
      description,
      datetime,
      location,
      capacity: capacity !== undefined ? (capacity === null ? null : Number(capacity)) : null,
      participants: [],
      status: 'open',
      pending_requests: [],
      denied_requests: [],
    };

    const { data: createdEvent, error } = await supabase
      .from('events')
      .insert(newEvent)
      .select()
      .single();

    if (error) {
      console.error('Supabase error creating event:', error);
      return NextResponse.json({ error: 'Failed to create event' }, { status: 500 });
    }

    return NextResponse.json(createdEvent, { status: 201 });
  } catch (error) {
    console.error('Error creating event:', error);
    return NextResponse.json({ error: 'Failed to create event' }, { status: 500 });
  }
}
