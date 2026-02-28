import os

files = {
    "app/api/admin/settings/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    // THE FIX: Select the exact row instead of generic keys
    const results: any = await query('SELECT * FROM settings ORDER BY id ASC LIMIT 1');
    const dbSettings = results && results.length > 0 ? results[0] : {};

    // Map the actual database columns to the frontend state
    const finalSettings = {
        site_name: dbSettings.site_name || 'Bank Management System',
        contact_email: dbSettings.contact_email || 'support@bank.com',
        site_logo: dbSettings.site_logo || '',
        primary_color: dbSettings.primary_color || '#2563EB',
        dark_mode_bg: dbSettings.dark_mode_bg || '#0f172a',
        max_transfer_limit: dbSettings.max_transfer_limit || '50000',
        allow_registrations: dbSettings.allow_registrations || 'true'
    };

    return NextResponse.json(finalSettings);
  } catch (error) {
    console.error("[SETTINGS GET ERROR]:", error);
    return NextResponse.json({ error: 'Failed to fetch settings' }, { status: 500 });
  }
}

export async function PUT(request: Request) {
  try {
    const session = await getSession();
    
    if (!session || session.role !== 'SuperAdmin') {
      return NextResponse.json({ error: 'Unauthorized: SuperAdmin access required' }, { status: 403 });
    }

    const data = await request.json();
    console.log("[SETTINGS PUT] Payload:", data);

    // 1. THE FIX: Dynamically add missing columns to TiDB so the query doesn't crash
    const columnsToAdd = [
        "ADD COLUMN contact_email VARCHAR(255) DEFAULT 'support@bank.com'",
        "ADD COLUMN primary_color VARCHAR(50) DEFAULT '#2563EB'",
        "ADD COLUMN dark_mode_bg VARCHAR(50) DEFAULT '#0f172a'",
        "ADD COLUMN max_transfer_limit VARCHAR(50) DEFAULT '50000'",
        "ADD COLUMN allow_registrations VARCHAR(10) DEFAULT 'true'"
    ];
    
    for (const col of columnsToAdd) {
        try {
            await query(`ALTER TABLE settings ${col}`);
        } catch (e) {
            // Column already exists, ignore and continue smoothly
        }
    }

    // 2. Ensure Row 1 exists before trying to update it
    const rows: any = await query('SELECT id FROM settings WHERE id = 1');
    if (rows.length === 0) {
        await query('INSERT INTO settings (id, site_name) VALUES (1, ?)', [data.site_name || 'Babji Bank']);
    }

    // 3. Dynamically build a safe UPDATE query for the exact columns provided
    const updates = [];
    const values = [];
    const allowedFields = ['site_name', 'contact_email', 'site_logo', 'primary_color', 'dark_mode_bg', 'max_transfer_limit', 'allow_registrations'];
    
    for (const [key, value] of Object.entries(data)) {
        if (allowedFields.includes(key) && value !== undefined && value !== null) {
            updates.push(`${key} = ?`);
            values.push(String(value));
        }
    }

    // 4. Execute the clean update
    if (updates.length > 0) {
        values.push(1); // Add the ID for the WHERE clause
        await query(`UPDATE settings SET ${updates.join(', ')} WHERE id = ?`, values);
    }

    return NextResponse.json({ message: 'Settings updated successfully' });
  } catch (error) {
    console.error("[SETTINGS PUT ERROR]:", error);
    return NextResponse.json({ error: 'Failed to update settings' }, { status: 500 });
  }
}
"""
}

def fix_schema_mismatch():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Settings API rewritten to match TiDB Columns!")

if __name__ == "__main__":
    fix_schema_mismatch()