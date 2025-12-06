import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

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
      return NextResponse.json({ error: 'Failed to approve request' }, { status: 500 });
    }

    const pendingRequests = event.pending_requests || [];
    const participants = event.participants || [];

    // Verify phone is in pending_requests
    if (!pendingRequests.includes(phone)) {
      return NextResponse.json(
        { error: 'Phone number not in pending requests' },
        { status: 400 }
      );
    }

    // Check capacity before approving
    if (event.capacity !== null && participants.length >= event.capacity) {
      return NextResponse.json(
        { error: 'Event is at full capacity' },
        { status: 400 }
      );
    }

    // Remove from pending_requests and add to participants
    const updatedPendingRequests = pendingRequests.filter((p: string) => p !== phone);
    const updatedParticipants = [...participants, phone];

    const { data: updatedEvent, error: updateError } = await supabase
      .from('events')
      .update({
        pending_requests: updatedPendingRequests,
        participants: updatedParticipants,
      })
      .eq('id', id)
      .select()
      .single();

    if (updateError) {
      console.error('Supabase error updating event:', updateError);
      return NextResponse.json({ error: 'Failed to approve request' }, { status: 500 });
    }

    return NextResponse.json(updatedEvent);
  } catch (error) {
    console.error('Error approving request:', error);
    return NextResponse.json({ error: 'Failed to approve request' }, { status: 500 });
  }
}
