import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';
import { sendMessage } from '@/lib/messaging';

// POST /api/events/[id]/join - Request to join event (requires host approval)
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

    // Check if user already joined (is a participant)
    const participants = event.participants || [];
    if (participants.includes(phone)) {
      return NextResponse.json(
        { error: 'Already joined this event' },
        { status: 400 }
      );
    }

    // Check if user already has a pending request
    const pendingRequests = event.pending_requests || [];
    if (pendingRequests.includes(phone)) {
      return NextResponse.json(
        { error: 'You already have a pending request for this event' },
        { status: 400 }
      );
    }

    // Check if user was denied (cannot re-apply per Section 18.2)
    const deniedRequests = event.denied_requests || [];
    if (deniedRequests.includes(phone)) {
      return NextResponse.json(
        { error: 'Your request for this event was denied and cannot be resubmitted' },
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

    // Get requester's name from users table
    const { data: userData } = await supabase
      .from('users')
      .select('name')
      .eq('phone', phone)
      .single();

    const requesterName = userData?.name || phone;

    // Add to pending_requests (NOT participants)
    const updatedPendingRequests = [...pendingRequests, phone];

    const { error: updateError } = await supabase
      .from('events')
      .update({ pending_requests: updatedPendingRequests })
      .eq('id', id);

    if (updateError) {
      console.error('Supabase error updating event:', updateError);
      return NextResponse.json({ error: 'Failed to submit join request' }, { status: 500 });
    }

    // Send notification to host (per Section 18.1)
    try {
      await sendMessage(
        event.host_phone,
        `${requesterName} is requesting to join "${event.title}". Reply 'approve ${requesterName}' or 'deny ${requesterName}'`
      );
    } catch (msgError) {
      console.error('Failed to send notification to host:', msgError);
      // Don't fail the request if notification fails - the request was still submitted
    }

    return NextResponse.json({
      status: 'pending',
      message: 'Request sent! Waiting for host approval.'
    });
  } catch (error) {
    console.error('Error joining event:', error);
    return NextResponse.json({ error: 'Failed to join event' }, { status: 500 });
  }
}
