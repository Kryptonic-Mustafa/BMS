import os

files = {
    "app/api/admin/settings/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  // THE FIX: Added ': any' so TypeScript knows this is an array with .forEach()
  const settings: any = await query('SELECT * FROM settings');
  const formatted: any = {};
  settings.forEach((s: any) => { formatted[s.setting_key] = s.setting_value; });
  
  return NextResponse.json(formatted);
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  
  if (session.role !== 'admin' && session.role !== 'SuperAdmin' && !session.permissions?.includes('SettingsManage') && !session.permissions?.includes('SettingsView')) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }

  const data = await request.json();
  for (const [key, value] of Object.entries(data)) {
      await query(
          'INSERT INTO settings (setting_key, setting_value) VALUES (?, ?) ON DUPLICATE KEY UPDATE setting_value = ?',
          [key, value, value]
      );
  }
  
  return NextResponse.json({ success: true });
}
"""
}

def fix_settings_ts():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Fixed Settings TypeScript Error!")

if __name__ == "__main__":
    fix_settings_ts()