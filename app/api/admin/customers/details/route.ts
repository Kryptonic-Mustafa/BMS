import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session || session.role !== 'admin') return NextResponse.json([], { status: 403 });

  // Fetch users with aggregated data
  const customers = await query(`
    SELECT u.id, u.name, u.email, u.created_at, 
           a.account_number, a.balance, 
           (SELECT COUNT(*) FROM transactions t WHERE t.account_id = a.id) as tx_count
    FROM users u
    LEFT JOIN accounts a ON u.id = a.user_id
    WHERE u.role = 'customer'
  `);

  return NextResponse.json(customers);
}