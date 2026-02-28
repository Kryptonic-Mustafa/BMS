import { NextResponse } from 'next/server';
import { query, pool } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function DELETE() {
  const session = await getSession();
  if (!session || !session.is_super_admin) {
    return NextResponse.json({ error: 'Super Admin access required' }, { status: 403 });
  }

  const connection = await pool.getConnection();
  try {
    await connection.beginTransaction();

    // 1. Delete all transactions
    await connection.query('DELETE FROM transactions');
    
    // 2. Delete all messages & tickets
    await connection.query('DELETE FROM messages');
    await connection.query('DELETE FROM support_tickets');
    await connection.query('DELETE FROM notifications');

    // 3. Delete all accounts
    await connection.query('DELETE FROM accounts');

    // 4. Delete all users EXCEPT Super Admins
    await connection.query('DELETE FROM users WHERE is_super_admin = FALSE');

    await connection.commit();
    return NextResponse.json({ success: true });
  } catch (error) {
    await connection.rollback();
    return NextResponse.json({ error: 'Reset failed' }, { status: 500 });
  } finally {
    connection.release();
  }
}