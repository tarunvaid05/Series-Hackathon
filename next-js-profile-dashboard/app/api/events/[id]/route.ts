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

// GET /api/events/[id] - Return single event by ID
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const events = readEvents();
    const event = events.find(e => e.id === id);

    if (!event) {
      return NextResponse.json({ error: 'Event not found' }, { status: 404 });
    }

    return NextResponse.json(event);
  } catch (error) {
    console.error('Error reading event:', error);
    return NextResponse.json({ error: 'Failed to read event' }, { status: 500 });
  }
}

// PUT /api/events/[id] - Update event
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();
    const events = readEvents();
    const eventIndex = events.findIndex(e => e.id === id);

    if (eventIndex === -1) {
      return NextResponse.json({ error: 'Event not found' }, { status: 404 });
    }

    // Only allow updating specific fields
    const allowedFields = ['title', 'description', 'datetime', 'location', 'capacity'];
    const updates: Partial<Event> = {};

    for (const field of allowedFields) {
      if (body[field] !== undefined) {
        if (field === 'capacity') {
          updates[field] = body[field] === null ? null : Number(body[field]);
        } else {
          (updates as Record<string, unknown>)[field] = body[field];
        }
      }
    }

    events[eventIndex] = { ...events[eventIndex], ...updates };
    writeEvents(events);

    return NextResponse.json(events[eventIndex]);
  } catch (error) {
    console.error('Error updating event:', error);
    return NextResponse.json({ error: 'Failed to update event' }, { status: 500 });
  }
}

// DELETE /api/events/[id] - Delete event
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const events = readEvents();
    const eventIndex = events.findIndex(e => e.id === id);

    if (eventIndex === -1) {
      return NextResponse.json({ error: 'Event not found' }, { status: 404 });
    }

    events.splice(eventIndex, 1);
    writeEvents(events);

    return NextResponse.json({ success: true, message: 'Event deleted' });
  } catch (error) {
    console.error('Error deleting event:', error);
    return NextResponse.json({ error: 'Failed to delete event' }, { status: 500 });
  }
}
