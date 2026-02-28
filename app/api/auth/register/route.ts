import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';

export async function POST(request: Request) {
  try {
    const { name, email, password } = await request.json();

    // 1. Check existing
    const existing: any = await query('SELECT id FROM users WHERE email = ?', [email]);
    if (existing.length > 0) return NextResponse.json({ error: 'Email already exists' }, { status: 400 });

    // 2. Generate Credentials
    const hashedPassword = await bcrypt.hash(password, 10);
    const pin = Math.floor(1000 + Math.random() * 9000).toString(); // Random 4-digit PIN
    const accountNumber = 'ACC' + Math.floor(1000000000 + Math.random() * 9000000000).toString();

    // 3. Create User
    const res: any = await query(
      'INSERT INTO users (name, email, password, role_id, pin) VALUES (?, ?, ?, 3, ?)',
      [name, email, hashedPassword, pin]
    );
    const userId = res.insertId;

    // 4. Create Account
    await query(
      'INSERT INTO accounts (user_id, account_number, balance, type, status) VALUES (?, ?, 0.00, "savings", "active")',
      [userId, accountNumber]
    );

    // 5. SEND WELCOME BANKMAIL
    const welcomeMsg = `
      Welcome to Dev Bank, ${name}!
      
      Here are your confidential account details:
      -----------------------------------------
      Account Number: ${accountNumber}
      Security PIN:   ${pin}
      -----------------------------------------
      
      Please keep your PIN safe. You will need it for all transfers.
      You can view this PIN anytime in your Profile.
    `;

    await query(
      'INSERT INTO messages (sender_id, receiver_id, subject, body) VALUES (0, ?, ?, ?)',
      [userId, 'Welcome to Dev Bank - Important Details', welcomeMsg]
    );

    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: 'Registration failed' }, { status: 500 });
  }
}