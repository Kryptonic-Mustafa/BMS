import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { accountId, amount } = await request.json();

  // 1. Get Account & User Details
  const acc: any = await query('SELECT u.id as user_id, u.name, u.email FROM accounts a JOIN users u ON a.user_id = u.id WHERE a.id = ?', [accountId]);
  if (acc.length === 0) return NextResponse.json({ error: 'Account not found' }, { status: 404 });
  const targetUser = acc[0];

  // 2. Perform Deposit
  await query('UPDATE accounts SET balance = balance + ? WHERE id = ?', [amount, accountId]);

  // 3. Create Transaction Record
  await query(
    'INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, ?, ?, ?, ?)',
    [accountId, 'credit', amount, 'completed', 'Admin Deposit']
  );

  // 4. AUDIT LOG (The New Part)
  await logActivity({
    actorId: session.id,
    actorName: session.name,
    targetId: targetUser.user_id,
    targetName: targetUser.name,
    action: 'ADMIN_DEPOSIT',
    details: `Deposited $${amount} into account`
  });

  return NextResponse.json({ success: true });
}