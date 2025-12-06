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

    const users = await readUsersFile();

    if (!users[phone]) {
      return NextResponse.json(
        { success: false, error: 'User not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      user: {
        phone,
        ...users[phone]
      }
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

    const users = await readUsersFile();

    if (!users[phone]) {
      return NextResponse.json(
        { success: false, error: 'User not found' },
        { status: 404 }
      );
    }

    // Only allow updating specific fields
    const allowedFields = ['name', 'bio', 'image', 'age'];
    const updates: Partial<User> = {};

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
          updates[field as keyof User] = age as never;
        } else {
          updates[field as keyof User] = body[field];
        }
      }
    }

    // Update user with new fields
    users[phone] = {
      ...users[phone],
      ...updates
    };

    await writeUsersFile(users);

    return NextResponse.json({
      success: true,
      user: {
        phone,
        ...users[phone]
      }
    });
  } catch (error) {
    console.error('Update user error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
