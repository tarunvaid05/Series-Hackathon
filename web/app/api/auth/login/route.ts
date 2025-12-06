import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

function validatePhoneNumber(phone: string): boolean {
  return typeof phone === 'string' && phone.startsWith('+');
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { phone } = body;

    if (!phone) {
      return NextResponse.json(
        { success: false, error: 'Phone number is required' },
        { status: 400 }
      );
    }

    if (!validatePhoneNumber(phone)) {
      return NextResponse.json(
        { success: false, error: 'Phone number must start with +' },
        { status: 400 }
      );
    }

    // Check if user exists
    const { data: existingUser, error: selectError } = await supabase
      .from('users')
      .select('*')
      .eq('phone', phone)
      .single();

    if (selectError && selectError.code !== 'PGRST116') {
      // PGRST116 = no rows returned (user not found)
      console.error('Supabase select error:', selectError);
      return NextResponse.json(
        { success: false, error: 'Internal server error' },
        { status: 500 }
      );
    }

    if (existingUser) {
      // User exists, return their profile
      return NextResponse.json({
        success: true,
        user: existingUser
      });
    }

    // User doesn't exist, create new user with default name "User"
    const { data: newUser, error: insertError } = await supabase
      .from('users')
      .insert({
        phone,
        name: 'User',
        registered_at: new Date().toISOString()
      })
      .select()
      .single();

    if (insertError) {
      console.error('Supabase insert error:', insertError);
      return NextResponse.json(
        { success: false, error: 'Internal server error' },
        { status: 500 }
      );
    }

    return NextResponse.json(
      {
        success: true,
        user: newUser,
        isNewUser: true
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
