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

// POST /api/events/[id]/approve - Approve a join request
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

    // Verify phone is in pending_requests
    if (!event.pending_requests.includes(phone)) {
      return NextResponse.json(
        { error: 'Phone number not in pending requests' },
        { status: 400 }
      );
    }

    // Check capacity before approving
    if (event.capacity !== null && event.participants.length >= event.capacity) {
      return NextResponse.json(
        { error: 'Event is at full capacity' },
        { status: 400 }
      );
    }

    // Remove from pending_requests
    event.pending_requests = event.pending_requests.filter(p => p !== phone);

    // Add to participants
    event.participants.push(phone);

    events[eventIndex] = event;
    writeEvents(events);

    return NextResponse.json(event);
  } catch (error) {
    console.error('Error approving request:', error);
    return NextResponse.json({ error: 'Failed to approve request' }, { status: 500 });
  }
}
