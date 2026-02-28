import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { merchantCode, amount, pin } = await request.json();

  // 1. Verify Merchant
  const merch: any = await query('SELECT * FROM merchants WHERE merchant_code = ?', [merchantCode]);
  if (merch.length === 0) return NextResponse.json({ error: 'Invalid QR Code / Merchant' }, { status: 404 });
  const merchant = merch[0];

  // 2. Verify User PIN & Balance
  const user: any = await query('SELECT pin, name FROM users WHERE id = ?', [session.id]);
  if (user[0].pin !== pin) return NextResponse.json({ error: 'Invalid Security PIN' }, { status: 400 });

  const acc: any = await query('SELECT id, balance FROM accounts WHERE user_id = ?', [session.id]);
  if (Number(acc[0].balance) < Number(amount)) return NextResponse.json({ error: 'Insufficient funds' }, { status: 400 });

  // 3. Execute Payment (Move money from User to Merchant Account)
  await query('UPDATE accounts SET balance = balance - ? WHERE id = ?', [amount, acc[0].id]);
  
  // 4. Log Transaction
  const tx: any = await query(
    'INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "debit", ?, "completed", ?)',
    [acc[0].id, amount, `Merchant Payment: ${merchant.business_name}`]
  );

  // 5. Notify & Audit
  await logActivity({
    actorId: session.id,
    actorName: session.name,
    action: 'MERCHANT_PAY',
    details: `Paid $${amount} to ${merchant.business_name} via QR`
  });

  await query(
    'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
    [session.id, `Payment of $${amount} to ${merchant.business_name} successful! 🛍️`, 'success']
  );

  return NextResponse.json({ success: true, merchant: merchant.business_name });
}