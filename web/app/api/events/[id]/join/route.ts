import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

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

// POST /api/events/[id]/join - Add user to event participants
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();

    const { phone } = body;

    if (!phone) {
      return NextResponse.json(
        { error: 'Missing required field: phone' },
        { status: 400 }
      );
    }

    const events = readEvents();
    const eventIndex = events.findIndex(e => e.id === id);

    if (eventIndex === -1) {
      return NextResponse.json({ error: 'Event not found' }, { status: 404 });
    }

    const event = events[eventIndex];

    // Check if user is the host
    if (event.host_phone === phone) {
      return NextResponse.json(
        { error: 'Host cannot join their own event' },
        { status: 400 }
      );
    }

    // Check if user already joined
    if (event.participants.includes(phone)) {
      return NextResponse.json(
        { error: 'Already joined this event' },
        { status: 400 }
      );
    }

    // Check capacity
    if (event.capacity !== null && event.participants.length >= event.capacity) {
      return NextResponse.json(
        { error: 'Event is at full capacity' },
        { status: 400 }
      );
    }

    // Add participant
    event.participants.push(phone);
    events[eventIndex] = event;
    writeEvents(events);

    return NextResponse.json(event);
  } catch (error) {
    console.error('Error joining event:', error);
    return NextResponse.json({ error: 'Failed to join event' }, { status: 500 });
  }
}
