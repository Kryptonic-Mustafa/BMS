import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const recentActivity = await query(
      'SELECT * FROM transactions WHERE account_id = (SELECT id FROM accounts WHERE user_id = ?) ORDER BY created_at DESC LIMIT 5',
      [session.id]
    );

    return NextResponse.json({ recentActivity });
  } catch (error) {
    console.error("Dashboard Fetch Error:", error);
    return NextResponse.json({ recentActivity: [] });
  }
}