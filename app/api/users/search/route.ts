import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  const { searchParams } = new URL(request.url);
  const q = searchParams.get('q') || '';

  if (q.length < 2) return NextResponse.json([]);

  // Search users by name or email (exclude self)
  const users = await query(
    'SELECT id, name, email FROM users WHERE (name LIKE ? OR email LIKE ?) AND id != ? LIMIT 5',
    [`%${q}%`, `%${q}%`, session.id]
  );
  
  return NextResponse.json(users);
}