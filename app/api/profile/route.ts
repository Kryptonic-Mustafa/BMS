import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const user: any = await query(
      'SELECT u.id, u.name, u.email, u.role_id, a.account_number, a.balance, a.type as account_type FROM users u LEFT JOIN accounts a ON u.id = a.user_id WHERE u.id = ?',
      [session.id]
    );

    if (user.length === 0) return NextResponse.json({ error: 'User not found' }, { status: 404 });

    return NextResponse.json(user[0]);
  } catch (error) {
    console.error("Profile API Error:", error);
    return NextResponse.json({ error: 'Failed to load profile' }, { status: 500 });
  }
}