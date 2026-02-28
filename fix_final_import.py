import os

files = {
    "app/api/notifications/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session'; // FIXED: Importing from session, not auth

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  const notifications = await query(
    'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 10',
    [session.id]
  );
  
  return NextResponse.json(notifications);
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  await query('UPDATE notifications SET is_read = TRUE WHERE user_id = ?', [session.id]);
  return NextResponse.json({ success: true });
}
"""
}

def fix_import():
    print("🔧 Fixing Notifications API Import...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n🎉 All Fixed! Restart your server.")

if __name__ == "__main__":
    fix_import()