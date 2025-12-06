import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

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

    // Fetch the event
    const { data: event, error: fetchError } = await supabase
      .from('events')
      .select('*')
      .eq('id', id)
      .single();

    if (fetchError) {
      if (fetchError.code === 'PGRST116') {
        return NextResponse.json({ error: 'Event not found' }, { status: 404 });
      }
      console.error('Supabase error fetching event:', fetchError);
      return NextResponse.json({ error: 'Failed to join event' }, { status: 500 });
    }

    // Check if user is the host
    if (event.host_phone === phone) {
      return NextResponse.json(
        { error: 'Host cannot join their own event' },
        { status: 400 }
      );
    }

    // Check if user already joined
    const participants = event.participants || [];
    if (participants.includes(phone)) {
      return NextResponse.json(
        { error: 'Already joined this event' },
        { status: 400 }
      );
    }

    // Check capacity
    if (event.capacity !== null && participants.length >= event.capacity) {
      return NextResponse.json(
        { error: 'Event is at full capacity' },
        { status: 400 }
      );
    }

    // Add participant
    const updatedParticipants = [...participants, phone];

    const { data: updatedEvent, error: updateError } = await supabase
      .from('events')
      .update({ participants: updatedParticipants })
      .eq('id', id)
      .select()
      .single();

    if (updateError) {
      console.error('Supabase error updating event:', updateError);
      return NextResponse.json({ error: 'Failed to join event' }, { status: 500 });
    }

    return NextResponse.json(updatedEvent);
  } catch (error) {
    console.error('Error joining event:', error);
    return NextResponse.json({ error: 'Failed to join event' }, { status: 500 });
  }
}
