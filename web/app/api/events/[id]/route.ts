import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';
import { notifyParticipants } from '@/lib/messaging';

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

// GET /api/events/[id] - Return single event by ID
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    const { data: event, error } = await supabase
      .from('events')
      .select('*')
      .eq('id', id)
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        return NextResponse.json({ error: 'Event not found' }, { status: 404 });
      }
      console.error('Supabase error reading event:', error);
      return NextResponse.json({ error: 'Failed to read event' }, { status: 500 });
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

    const { data: updatedEvent, error } = await supabase
      .from('events')
      .update(updates)
      .eq('id', id)
      .select()
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        return NextResponse.json({ error: 'Event not found' }, { status: 404 });
      }
      console.error('Supabase error updating event:', error);
      return NextResponse.json({ error: 'Failed to update event' }, { status: 500 });
    }

    // Notify participants about the update (non-blocking)
    if (updatedEvent.participants && updatedEvent.participants.length > 0) {
      notifyParticipants(
        updatedEvent.participants,
        `Event "${updatedEvent.title}" has been updated. Check the new details!`
      ).catch(error => {
        console.error('Failed to notify participants about update:', error);
      });
    }

    return NextResponse.json(updatedEvent);
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

    // First fetch the event to get participant info for notification
    const { data: eventToDelete, error: fetchError } = await supabase
      .from('events')
      .select('*')
      .eq('id', id)
      .single();

    if (fetchError) {
      if (fetchError.code === 'PGRST116') {
        return NextResponse.json({ error: 'Event not found' }, { status: 404 });
      }
      console.error('Supabase error fetching event:', fetchError);
      return NextResponse.json({ error: 'Failed to delete event' }, { status: 500 });
    }

    // Notify participants about cancellation (non-blocking)
    if (eventToDelete.participants && eventToDelete.participants.length > 0) {
      notifyParticipants(
        eventToDelete.participants,
        `Event "${eventToDelete.title}" has been cancelled by the host.`
      ).catch(error => {
        console.error('Failed to notify participants about cancellation:', error);
      });
    }

    // Now delete the event
    const { error: deleteError } = await supabase
      .from('events')
      .delete()
      .eq('id', id);

    if (deleteError) {
      console.error('Supabase error deleting event:', deleteError);
      return NextResponse.json({ error: 'Failed to delete event' }, { status: 500 });
    }

    return NextResponse.json({ success: true, message: 'Event deleted' });
  } catch (error) {
    console.error('Error deleting event:', error);
    return NextResponse.json({ error: 'Failed to delete event' }, { status: 500 });
  }
}
