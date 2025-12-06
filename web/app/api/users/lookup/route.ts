import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

const DATA_DIR = path.join(process.cwd(), '..', 'data');
const USERS_FILE = path.join(DATA_DIR, 'users.json');

interface User {
  name: string;
  registered_at: string;
  bio?: string;
  image?: string;
  age?: number;
}

interface UsersData {
  [phone: string]: User;
}

interface UserLookupResult {
  [phone: string]: { name: string };
}

async function readUsersFile(): Promise<UsersData> {
  try {
    const content = await fs.readFile(USERS_FILE, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      return {};
    }
    throw error;
  }
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

    const users = await readUsersFile();
    const result: UserLookupResult = {};

    for (const phone of phones) {
      if (users[phone]) {
        result[phone] = { name: users[phone].name };
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
