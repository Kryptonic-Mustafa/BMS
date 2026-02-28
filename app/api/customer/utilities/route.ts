import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export const dynamic = 'force-dynamic';

export async function GET() {
  const providers = await query('SELECT * FROM utility_providers ORDER BY category ASC');
  return NextResponse.json(providers);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { providerId, consumerNumber, amount, pin } = await request.json();

  // 1. Verify PIN & Balance
  const user: any = await query('SELECT pin FROM users WHERE id = ?', [session.id]);
  if (user[0].pin !== pin) return NextResponse.json({ error: 'Invalid Security PIN' }, { status: 400 });

  const acc: any = await query('SELECT id, balance FROM accounts WHERE user_id = ?', [session.id]);
  if (Number(acc[0].balance) < Number(amount)) return NextResponse.json({ error: 'Insufficient funds' }, { status: 400 });

  // 2. Execute Payment
  await query('UPDATE accounts SET balance = balance - ? WHERE id = ?', [amount, acc[0].id]);
  
  // 3. Log Transaction
  const provider: any = await query('SELECT name FROM utility_providers WHERE id = ?', [providerId]);
  const tx: any = await query(
    'INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "debit", ?, "completed", ?)',
    [acc[0].id, amount, `Bill Pay: ${provider[0].name} (${consumerNumber})`]
  );

  // 4. Record Bill
  await query(
    'INSERT INTO bill_payments (user_id, provider_id, consumer_number, amount, transaction_id) VALUES (?, ?, ?, ?, ?)',
    [session.id, providerId, consumerNumber, amount, tx.insertId]
  );

  // 5. Notify & Audit
  await logActivity({
    actorId: session.id,
    actorName: session.name,
    action: 'BILL_PAY',
    details: `Paid $${amount} to ${provider[0].name}`
  });

  await query(
    'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
    [session.id, `Payment of $${amount} to ${provider[0].name} was successful.`, 'success']
  );

  return NextResponse.json({ success: true });
}