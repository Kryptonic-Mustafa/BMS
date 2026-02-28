import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session'; // FIXED: Imported from session, not auth

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  
  const { searchParams } = new URL(request.url);
  const q = searchParams.get('q') || '';
  
  const users = await query(
    'SELECT id, name, email FROM users WHERE name LIKE ? OR email LIKE ? LIMIT 10', 
    [`%${q}%`, `%${q}%`]
  );
  return NextResponse.json(users);
}