import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session || session.role !== 'SuperAdmin') {
      return NextResponse.json({ error: 'Unauthorized: SuperAdmin access required' }, { status: 403 });
    }

    const { password, action } = await request.json();

    // 1. Verify SuperAdmin password against TiDB
    const users: any = await query('SELECT password FROM users WHERE id = ?', [session.id]);
    if (users.length === 0) return NextResponse.json({ error: 'User not found' }, { status: 404 });

    const isMatch = await bcrypt.compare(password, users[0].password);
    if (!isMatch) return NextResponse.json({ error: 'Incorrect password. Action denied.' }, { status: 401 });

    // 2. Execute requested Danger Action safely
    if (action === 'wipe_transactions') {
        await query('TRUNCATE TABLE transactions');
        await query('UPDATE accounts SET balance = 0');
    } else if (action === 'reset_kyc') {
        await query("UPDATE users SET kyc_status = 'unverified' WHERE role_id != 1");
    }

    return NextResponse.json({ message: 'Action completed successfully' });
  } catch (error) {
    console.error('[DANGER API ERROR]:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}