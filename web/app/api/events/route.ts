import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { randomUUID } from 'crypto';

const DATA_DIR = path.join(process.cwd(), '..', 'data');
const EVENTS_FILE = path.join(DATA_DIR, 'events.json');

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
}

function readEvents(): Event[] {
  try {
    const data = fs.readFileSync(EVENTS_FILE, 'utf-8');
    return JSON.parse(data);
  } catch {
    return [];
  }
}

function writeEvents(events: Event[]): void {
  fs.writeFileSync(EVENTS_FILE, JSON.stringify(events, null, 2));
}

// GET /api/events - Return all events (optionally filter by query params)
export async function GET(request: NextRequest) {
  try {
    const events = readEvents();
    const { searchParams } = new URL(request.url);

    let filteredEvents = events;

    // Filter by host_phone if provided
    const hostPhone = searchParams.get('host_phone');
    if (hostPhone) {
      filteredEvents = filteredEvents.filter(e => e.host_phone === hostPhone);
    }

    // Filter by status if provided
    const status = searchParams.get('status');
    if (status === 'open' || status === 'closed') {
      filteredEvents = filteredEvents.filter(e => e.status === status);
    }

    // Filter by participant phone if provided
    const participant = searchParams.get('participant');
    if (participant) {
      filteredEvents = filteredEvents.filter(e => e.participants.includes(participant));
    }

    return NextResponse.json(filteredEvents);
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

    const events = readEvents();

    const newEvent: Event = {
      id: randomUUID(),
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

    events.push(newEvent);
    writeEvents(events);

    return NextResponse.json(newEvent, { status: 201 });
  } catch (error) {
    console.error('Error creating event:', error);
    return NextResponse.json({ error: 'Failed to create event' }, { status: 500 });
  }
}
