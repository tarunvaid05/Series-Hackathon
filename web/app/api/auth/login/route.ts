import { promises as fs } from 'fs';
import path from 'path';
import { NextRequest, NextResponse } from 'next/server';

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

async function writeUsersFile(data: UsersData): Promise<void> {
  await fs.writeFile(USERS_FILE, JSON.stringify(data, null, 2), 'utf-8');
}

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

    const users = await readUsersFile();

    if (users[phone]) {
      // User exists, return their profile
      return NextResponse.json({
        success: true,
        user: {
          phone,
          ...users[phone]
        }
      });
    }

    // User doesn't exist, create new user with phone as name
    const newUser: User = {
      name: phone,
      registered_at: new Date().toISOString()
    };

    users[phone] = newUser;
    await writeUsersFile(users);

    return NextResponse.json(
      {
        success: true,
        user: {
          phone,
          ...newUser
        }
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
