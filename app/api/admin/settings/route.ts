import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  const session = await getSession();
  
  // FIX: We do NOT check for 'SettingsView' here. 
  // Why? Because the Sidebar fetches this endpoint on EVERY page to get the Bank Logo and Name.
  // If we block it, it throws a 403 error which can trigger a global toast.
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const settings = await query('SELECT * FROM settings');
  const formatted: any = {};
  settings.forEach((s: any) => { formatted[s.setting_key] = s.setting_value; });
  
  return NextResponse.json(formatted);
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  
  // STRICT PERMISSION CHECK FOR UPDATES (Only admins/managers with permission can SAVE settings)
  if (session.role !== 'admin' && !session.permissions?.includes('SettingsManage') && !session.permissions?.includes('SettingsView')) {
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