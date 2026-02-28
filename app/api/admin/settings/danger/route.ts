import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session || session.role !== 'SuperAdmin') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
    }

    const { action, password, userIds, resetType } = await request.json();

    // 1. Strict Password Verification for ALL Danger Actions
    const users: any = await query('SELECT password FROM users WHERE id = ?', [session.id]);
    if (users.length === 0) return NextResponse.json({ error: 'Session invalid' }, { status: 401 });

    const isMatch = await bcrypt.compare(password, users[0].password);
    if (!isMatch) return NextResponse.json({ error: 'Incorrect SuperAdmin password.' }, { status: 401 });

    // 2. ACTION: Fetch Users & Accounts for the Selection Modal
    if (action === 'fetch_users') {
        const customerList = await query('SELECT id, name, email FROM users WHERE role_id != 1 AND is_super_admin = 0');
        const accountList = await query('SELECT user_id, account_number, balance FROM accounts');
        return NextResponse.json({ users: customerList, accounts: accountList });
    }

    // 3. ACTION: Targeted User Deletion (Safely handling Foreign Keys)
    if (action === 'delete_users') {
        if (!userIds || userIds.length === 0) return NextResponse.json({ error: 'No users selected' }, { status: 400 });
        
        const placeholders = userIds.map(() => '?').join(',');
        
        // Delete dependent data first to prevent constraint crashes
        await query(`DELETE FROM accounts WHERE user_id IN (${placeholders})`, userIds);
        await query(`DELETE FROM users WHERE id IN (${placeholders})`, userIds);
        
        return NextResponse.json({ message: `Successfully deleted ${userIds.length} user(s).` });
    }

    // 4. ACTION: Granular System Reset
    if (action === 'factory_reset') {
        if (resetType === 'data' || resetType === 'both') {
            await query('UPDATE accounts SET balance = 0');
        }
        if (resetType === 'users' || resetType === 'both') {
            await query('DELETE FROM accounts WHERE user_id IN (SELECT id FROM users WHERE role_id != 1 AND is_super_admin = 0)');
            await query('DELETE FROM users WHERE role_id != 1 AND is_super_admin = 0');
        }
        return NextResponse.json({ message: `System reset (${resetType}) executed successfully.` });
    }

    return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
  } catch (error) {
    console.error('[DANGER API ERROR]:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}