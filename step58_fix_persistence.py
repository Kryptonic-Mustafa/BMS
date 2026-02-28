import os

files = {
    "app/api/profile/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import bcrypt from 'bcryptjs';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({});

  const user: any = await query(`
    SELECT u.id, u.name, u.email, u.role, u.pin, u.auto_statements, a.account_number, a.balance 
    FROM users u
    LEFT JOIN accounts a ON u.id = a.user_id
    WHERE u.id = ?
  `, [session.id]);

  if (user.length === 0) return NextResponse.json({ error: 'User not found' });
  return NextResponse.json(user[0]);
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const body = await request.json();

  // 1. Handle Auto-Statement Toggle (The Fix)
  if (body.action === 'toggle_auto_statements') {
      const val = body.value ? 1 : 0;
      await query('UPDATE users SET auto_statements = ? WHERE id = ?', [val, session.id]);
      return NextResponse.json({ success: true });
  }

  // 2. Reveal PIN
  if (body.action === 'reveal_pin') {
      const { password } = body;
      const u: any = await query('SELECT password, pin FROM users WHERE id = ?', [session.id]);
      const isMatch = await bcrypt.compare(password, u[0].password);
      if (!isMatch) return NextResponse.json({ error: 'Incorrect Password' }, { status: 401 });
      return NextResponse.json({ success: true, pin: u[0].pin });
  }

  // 3. Update Profile
  if (body.action === 'update_info') {
      const { name, email } = body;
      await query('UPDATE users SET name = ?, email = ? WHERE id = ?', [name, email, session.id]);
      return NextResponse.json({ success: true });
  }

  return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
}
"""
}

def fix_persistence():
    print("💾 Fixing Preference Persistence for Auto-Statements...")
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    fix_persistence()