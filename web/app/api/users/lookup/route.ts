import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

interface UserLookupResult {
  [phone: string]: { name: string };
}

// POST /api/users/lookup - Bulk lookup user names by phone numbers
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const { phones } = body;

    if (!phones || !Array.isArray(phones)) {
      return NextResponse.json(
        { error: 'Missing required field: phones (array)' },
        { status: 400 }
      );
    }

    const { data: users, error } = await supabase
      .from('users')
      .select('phone, name')
      .in('phone', phones);

    if (error) {
      console.error('Supabase lookup error:', error);
      return NextResponse.json({ error: 'Failed to lookup users' }, { status: 500 });
    }

    // Build result map
    const result: UserLookupResult = {};
    const foundPhones = new Set(users?.map(u => u.phone) || []);

    for (const phone of phones) {
      const user = users?.find(u => u.phone === phone);
      if (user) {
        result[phone] = { name: user.name };
      } else {
        result[phone] = { name: 'Unknown' };
      }
    }

    return NextResponse.json(result);
  } catch (error) {
    console.error('Error looking up users:', error);
    return NextResponse.json({ error: 'Failed to lookup users' }, { status: 500 });
  }
}
