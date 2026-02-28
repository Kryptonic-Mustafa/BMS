import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ customers: 0, holdings: 0, transactions: 0 });

  // 1. Total Customers (Role ID 3)
  const users: any = await query('SELECT COUNT(*) as count FROM users WHERE role_id = 3');
  
  // 2. Total Holdings (Sum of all account balances)
  const money: any = await query('SELECT SUM(balance) as total FROM accounts');
  
  // 3. Total Transactions
  const tx: any = await query('SELECT COUNT(*) as count FROM transactions');

  return NextResponse.json({
    customers: users[0].count || 0,
    holdings: money[0].total || 0,
    transactions: tx[0].count || 0
  });
}