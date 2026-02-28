import os

files = {
    # 1. FIX THE 500 ERROR: Change POST to PUT to match your frontend request
    "app/api/admin/settings/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const results: any = await query('SELECT setting_key, setting_value FROM settings');
    
    const settingsObj: Record<string, string> = {};
    if (results && results.length > 0) {
        results.forEach((row: any) => {
            settingsObj[row.setting_key] = row.setting_value;
        });
    }

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

// THE MAJOR FIX: Exported as PUT to satisfy the frontend's fetch request
export async function PUT(request: Request) {
  try {
    const session = await getSession();
    
    if (!session || session.role !== 'SuperAdmin') {
      return NextResponse.json({ error: 'Unauthorized: SuperAdmin access required' }, { status: 403 });
    }

    const data = await request.json();

    try {
        await query('ALTER TABLE settings ADD UNIQUE INDEX unique_setting_key (setting_key)');
    } catch (e) {
        // Ignore if index already exists
    }

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
    console.error("[SETTINGS PUT ERROR]:", error);
    return NextResponse.json({ error: 'Failed to update settings' }, { status: 500 });
  }
}
""",

    # 2. FIX THE 404 ERROR: Dynamically generates a beautiful 'B' Favicon for Babji Bank
    "app/icon.tsx": """
import { ImageResponse } from 'next/og';

export const runtime = 'edge';
export const size = { width: 32, height: 32 };
export const contentType = 'image/png';

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          fontSize: 24,
          background: '#2563EB',
          color: 'white',
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '8px',
          fontWeight: 'bold'
        }}
      >
        B
      </div>
    ),
    { ...size }
  );
}
""",

    # 3. FIX THE HYDRATION ERROR: Suppresses warnings caused by browser extensions like LastPass
    "app/(dashboard)/layout.tsx": """
import Sidebar from '@/components/layout/Sidebar';
import { Navbar } from '@/components/layout/Navbar';
import { getSession } from '@/lib/session';
import { redirect } from 'next/navigation';

export const dynamic = 'force-dynamic';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getSession();

  if (!session) {
    redirect('/login');
  }

  return (
    // THE FIX: suppressHydrationWarning stops React from panicking when browser extensions alter the DOM
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900" suppressHydrationWarning>
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden pl-64">
        <Navbar user={session} />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-50 dark:bg-slate-900 p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
"""
}

def apply_clean_console():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ API Method fixed to PUT, Favicon generated, and Hydration Warnings suppressed!")

if __name__ == "__main__":
    apply_clean_console()