import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  const logs = await query(
    'SELECT * FROM login_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 10',
    [session.id]
  );
  return NextResponse.json(logs);
}