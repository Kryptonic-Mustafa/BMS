import os

files = {
    "app/api/notifications/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json([], { status: 200 });

    const notifications: any = await query(
      'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 20',
      [session.id]
    );

    return NextResponse.json(notifications || []);
  } catch (error) {
    console.error("Notifications API Error:", error);
    // Return empty array instead of 500 to keep UI stable
    return NextResponse.json([]);
  }
}
""",
    "app/api/profile/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const user: any = await query(
      'SELECT u.id, u.name, u.email, u.role_id, a.account_number, a.balance, a.type as account_type FROM users u LEFT JOIN accounts a ON u.id = a.user_id WHERE u.id = ?',
      [session.id]
    );

    if (user.length === 0) return NextResponse.json({ error: 'User not found' }, { status: 404 });

    return NextResponse.json(user[0]);
  } catch (error) {
    console.error("Profile API Error:", error);
    return NextResponse.json({ error: 'Failed to load profile' }, { status: 500 });
  }
}
"""
}

def fix_prod_apis():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Patched Notifications and Profile APIs for Production!")

if __name__ == "__main__":
    fix_prod_apis()