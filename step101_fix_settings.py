import os

files = {
    "app/api/admin/settings/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    // 1. Fetch all rows from the settings table
    const results: any = await query('SELECT setting_key, setting_value FROM settings');
    
    // 2. Convert database rows into a flat JSON object for the frontend to pre-fill
    const settingsObj: Record<string, string> = {};
    if (results && results.length > 0) {
        results.forEach((row: any) => {
            settingsObj[row.setting_key] = row.setting_value;
        });
    }

    // 3. Provide safe defaults if the database is empty to prevent Hydration Error #418
    const finalSettings = {
        site_name: settingsObj.site_name || 'Bank Management System',
        contact_email: settingsObj.contact_email || 'support@bank.com',
        site_logo: settingsObj.site_logo || '',
        primary_color: settingsObj.primary_color || '#2563EB',
        dark_mode_bg: settingsObj.dark_mode_bg || '#0f172a',
        max_transfer_limit: settingsObj.max_transfer_limit || '50000',
        allow_registrations: settingsObj.allow_registrations || 'true'
    };

    return NextResponse.json(finalSettings);
  } catch (error) {
    console.error("[SETTINGS GET ERROR]:", error);
    return NextResponse.json({ error: 'Failed to fetch settings' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const session = await getSession();
    
    // Security check: Only SuperAdmins can change master settings
    if (!session || session.role !== 'SuperAdmin') {
      return NextResponse.json({ error: 'Unauthorized: SuperAdmin access required' }, { status: 403 });
    }

    const data = await request.json();
    console.log("[SETTINGS POST] Received payload:", data);

    // Ensure the table has a unique constraint so ON DUPLICATE KEY UPDATE works in TiDB
    try {
        await query('ALTER TABLE settings ADD UNIQUE INDEX unique_setting_key (setting_key)');
    } catch (e) {
        // Ignore error if the index already exists
    }

    // Iterate through the payload and safely update or insert each setting
    for (const [key, value] of Object.entries(data)) {
      if (value !== undefined && value !== null) {
         await query(
           'INSERT INTO settings (setting_key, setting_value) VALUES (?, ?) ON DUPLICATE KEY UPDATE setting_value = ?',
           [key, String(value), String(value)]
         );
      }
    }

    return NextResponse.json({ message: 'Settings updated successfully' });
  } catch (error) {
    console.error("[SETTINGS POST ERROR]:", error);
    return NextResponse.json({ error: 'Failed to update settings' }, { status: 500 });
  }
}
"""
}

def fix_settings_api():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Settings API fortified for TiDB and Hydration Error mitigated!")

if __name__ == "__main__":
    fix_settings_api()