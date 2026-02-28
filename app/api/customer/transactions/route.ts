import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  // 1. Get User's Account ID
  const acc: any = await query('SELECT id FROM accounts WHERE user_id = ? LIMIT 1', [session.id]);
  if (acc.length === 0) return NextResponse.json([]); // No account yet

  // 2. Fetch Transactions (Both Credit & Debit)
  // We limit to 20 for history page, or 5 for dashboard
  const transactions = await query(`
    SELECT * FROM transactions 
    WHERE account_id = ? 
    ORDER BY created_at DESC 
    LIMIT 20
  `, [acc[0].id]);

  return NextResponse.json(transactions);
}