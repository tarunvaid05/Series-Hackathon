import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

function validatePhoneNumber(phone: string): boolean {
  return typeof phone === 'string' && phone.startsWith('+');
}

interface RouteContext {
  params: Promise<{ phone: string }>;
}

export async function GET(
  request: NextRequest,
  context: RouteContext
) {
  try {
    const { phone } = await context.params;

    if (!validatePhoneNumber(phone)) {
      return NextResponse.json(
        { success: false, error: 'Phone number must start with +' },
        { status: 400 }
      );
    }

    const { data: user, error } = await supabase
      .from('users')
      .select('*')
      .eq('phone', phone)
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        // No rows returned
        return NextResponse.json(
          { success: false, error: 'User not found' },
          { status: 404 }
        );
      }
      console.error('Supabase select error:', error);
      return NextResponse.json(
        { success: false, error: 'Internal server error' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      user
    });
  } catch (error) {
    console.error('Get user error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  context: RouteContext
) {
  try {
    const { phone } = await context.params;
    const body = await request.json();

    if (!validatePhoneNumber(phone)) {
      return NextResponse.json(
        { success: false, error: 'Phone number must start with +' },
        { status: 400 }
      );
    }

    // Check if user exists
    const { data: existingUser, error: checkError } = await supabase
      .from('users')
      .select('phone')
      .eq('phone', phone)
      .single();

    if (checkError) {
      if (checkError.code === 'PGRST116') {
        return NextResponse.json(
          { success: false, error: 'User not found' },
          { status: 404 }
        );
      }
      console.error('Supabase check error:', checkError);
      return NextResponse.json(
        { success: false, error: 'Internal server error' },
        { status: 500 }
      );
    }

    // Only allow updating specific fields
    const allowedFields = ['name', 'bio', 'image', 'age'];
    const updates: Record<string, string | number | null> = {};

    for (const field of allowedFields) {
      if (body[field] !== undefined) {
        if (field === 'age' && body[field] !== null) {
          const age = Number(body[field]);
          if (isNaN(age) || age < 0) {
            return NextResponse.json(
              { success: false, error: 'Age must be a valid positive number' },
              { status: 400 }
            );
          }
          updates[field] = age;
        } else {
          updates[field] = body[field];
        }
      }
    }

    // Update user with new fields
    const { data: updatedUser, error: updateError } = await supabase
      .from('users')
      .update(updates)
      .eq('phone', phone)
      .select()
      .single();

    if (updateError) {
      console.error('Supabase update error:', updateError);
      return NextResponse.json(
        { success: false, error: 'Internal server error' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      user: updatedUser
    });
  } catch (error) {
    console.error('Update user error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
