import os

files = {
    # --- 1. UPDATE LOGIN API (Log Logins) ---
    "app/api/auth/login/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { encrypt } from '@/lib/auth';
import { cookies } from 'next/headers';
import { decryptData } from '@/lib/crypto';
import { logActivity } from '@/lib/audit'; // Import Logger

export async function POST(request: Request) {
  try {
    const rawBody = await request.json();
    const body = rawBody.data ? decryptData(rawBody.data) : rawBody;
    if (!body) return NextResponse.json({ error: 'Invalid payload' }, { status: 400 });

    const { email, password } = body;

    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    
    const user = users[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });

    // --- LOG ACTIVITY HERE ---
    await logActivity({
        actorId: user.id,
        actorName: user.name,
        action: 'USER_LOGIN',
        details: 'User logged in successfully'
    });

    // ... Rest of the login logic ...
    let permissions: string[] = [];
    if (user.role_id) {
        const perms: any = await query(`
            SELECT p.name FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = ?
        `, [user.role_id]);
        permissions = perms.map((p: any) => p.name);
    }

    const sessionData = {
      id: user.id,
      name: user.name,
      email: user.email,
      role_id: user.role_id,
      role: user.role,
      is_super_admin: user.is_super_admin === 1
    };

    const cookieStore = await cookies();
    const token = await encrypt(sessionData);
    cookieStore.set('session', token, { httpOnly: true, secure: process.env.NODE_ENV === 'production', maxAge: 60 * 60 * 24, path: '/', });

    const clientPolicy = JSON.stringify({ role: user.role, permissions });
    cookieStore.set('client_policy', clientPolicy, { httpOnly: false, secure: process.env.NODE_ENV === 'production', maxAge: 60 * 60 * 24, path: '/' });

    return NextResponse.json({ message: 'Login successful', user: sessionData });
  } catch (error) {
    return NextResponse.json({ error: 'Login failed' }, { status: 500 });
  }
}
""",

    # --- 2. UPDATE TRANSFER API (Log Transfers) ---
    "app/api/customer/transfer/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import bcrypt from 'bcryptjs';
import { logActivity } from '@/lib/audit'; // Import Logger

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { amount, accountNumber, pin } = await request.json();

  // 1. Verify User & Balance
  const users: any = await query('SELECT * FROM users WHERE id = ?', [session.id]);
  const user = users[0];

  const isPinValid = await bcrypt.compare(pin, user.pin);
  if (!isPinValid) return NextResponse.json({ error: 'Invalid PIN' }, { status: 400 });

  const senderAcc: any = await query('SELECT * FROM accounts WHERE user_id = ?', [session.id]);
  if (senderAcc.length === 0 || senderAcc[0].balance < amount) {
    return NextResponse.json({ error: 'Insufficient funds' }, { status: 400 });
  }

  // 2. Find Receiver
  const receiverAcc: any = await query('SELECT * FROM accounts WHERE account_number = ?', [accountNumber]);
  if (receiverAcc.length === 0) return NextResponse.json({ error: 'Receiver not found' }, { status: 404 });

  // 3. Execute Transfer
  await query('UPDATE accounts SET balance = balance - ? WHERE id = ?', [amount, senderAcc[0].id]);
  await query('UPDATE accounts SET balance = balance + ? WHERE id = ?', [amount, receiverAcc[0].id]);

  // 4. Record Transactions
  await query('INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "debit", ?, "completed", ?)', 
    [senderAcc[0].id, amount, `Transfer to ${accountNumber}`]);
    
  await query('INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "credit", ?, "completed", ?)', 
    [receiverAcc[0].id, amount, `Received from ${user.name}`]);

  // --- 5. LOG ACTIVITY ---
  await logActivity({
    actorId: session.id,
    actorName: session.name,
    targetId: receiverAcc[0].user_id, // We don't have receiver name easily here, logic handles fallback
    action: 'MONEY_TRANSFER',
    details: `Transferred $${amount} to Account ${accountNumber}`
  });

  return NextResponse.json({ success: true });
}
"""
}

def fix_logging():
    print("🔧 Fixing Database & Instrumenting Logger...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✅ Logger Installed on Login & Transfer!")

if __name__ == "__main__":
    fix_logging()