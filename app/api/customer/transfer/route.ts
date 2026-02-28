import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { amount, accountNumber, pin, otp, addToReceiver } = await request.json();

    // 1. Verify User & PIN
    const users: any = await query('SELECT pin, name FROM users WHERE id = ?', [session.id]);
    if (users[0].pin !== pin) return NextResponse.json({ error: 'Invalid Security PIN' }, { status: 400 });

    // 2. VERIFY OTP (The Smart Part)
    const otpCheck: any = await query(
        'SELECT * FROM otp_codes WHERE user_id = ? AND code = ? AND expires_at > CURRENT_TIMESTAMP',
        [session.id, otp]
    );

    if (otpCheck.length === 0) {
        return NextResponse.json({ 
            error: 'Invalid or Expired OTP. If funds were debited, they will be refunded within 3 days.' 
        }, { status: 400 });
    }

    // 3. Balance Check
    const senderAcc: any = await query('SELECT id, balance, account_number FROM accounts WHERE user_id = ?', [session.id]);
    if (Number(senderAcc[0].balance) < Number(amount)) {
        return NextResponse.json({ error: 'Insufficient funds' }, { status: 400 });
    }

    // 4. Find Receiver
    const receiverAcc: any = await query('SELECT id, user_id FROM accounts WHERE account_number = ?', [accountNumber]);
    if (receiverAcc.length === 0) return NextResponse.json({ error: 'Receiver not found' }, { status: 404 });

    // 5. Execute Transfer
    await query('UPDATE accounts SET balance = balance - ? WHERE id = ?', [amount, senderAcc[0].id]);
    await query('UPDATE accounts SET balance = balance + ? WHERE id = ?', [amount, receiverAcc[0].id]);

    // 6. Logs & Cleanup
    await query('DELETE FROM otp_codes WHERE user_id = ?', [session.id]);
    await query('INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "debit", ?, "completed", ?)', 
        [senderAcc[0].id, amount, `Transfer to ${accountNumber}`]);

    // Reciprocal Beneficiary Logic
    if (addToReceiver) {
        const exists: any = await query('SELECT id FROM beneficiaries WHERE user_id = ? AND account_number = ?', [receiverAcc[0].user_id, senderAcc[0].account_number]);
        if (exists.length === 0) {
            await query('INSERT INTO beneficiaries (user_id, saved_name, account_number) VALUES (?, ?, ?)', [receiverAcc[0].user_id, users[0].name, senderAcc[0].account_number]);
        }
    }

    return NextResponse.json({ success: true });
  } catch (e) {
    return NextResponse.json({ error: 'Transaction failed' }, { status: 500 });
  }
}