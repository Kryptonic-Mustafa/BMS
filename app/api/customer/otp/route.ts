import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { action } = await request.json();

  if (action === 'request') {
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    await query('DELETE FROM otp_codes WHERE user_id = ?', [session.id]);
    await query('INSERT INTO otp_codes (user_id, code) VALUES (?, ?)', [session.id, code]);
    
    // Simulate sending via BankMail/Notification
    await query(
      'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
      [session.id, `SECURITY: Your One-Time Password is ${code}. It expires in 5 minutes.`, 'error']
    );
    return NextResponse.json({ success: true, message: 'OTP Sent to your notification bell' });
  }
  return NextResponse.json({ error: 'Invalid action' });
}