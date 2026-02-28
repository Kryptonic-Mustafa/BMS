import os

files = {
    "app/api/customer/otp/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { action } = await request.json();

  if (action === 'request') {
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    
    // Clear old OTPs
    await query('DELETE FROM otp_codes WHERE user_id = ?', [session.id]);
    
    // THE FIX: We calculate the 5-minute expiry directly in the INSERT statement
    await query(
      'INSERT INTO otp_codes (user_id, code, expires_at) VALUES (?, ?, DATE_ADD(NOW(), INTERVAL 5 MINUTE))', 
      [session.id, code]
    );
    
    // Send Notification
    await query(
      'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
      [session.id, `SECURITY: Your One-Time Password is ${code}. It expires in 5 minutes.`, 'error']
    );
    
    return NextResponse.json({ success: true, message: 'OTP Sent to your notification bell' });
  }
  
  return NextResponse.json({ error: 'Invalid action' });
}
"""
}

def fix_otp_api():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Fixed OTP API to handle 5-minute Expiry dynamically!")

if __name__ == "__main__":
    fix_otp_api()