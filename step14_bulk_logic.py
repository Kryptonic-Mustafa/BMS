import os

files = {
    # --- 1. NEW BULK DELETE API ---
    "app/api/admin/users/bulk-delete/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session || !session.is_super_admin) {
    return NextResponse.json({ error: 'Super Admin access required' }, { status: 403 });
  }

  const { ids } = await request.json();

  if (!Array.isArray(ids) || ids.length === 0) {
    return NextResponse.json({ error: 'No IDs provided' }, { status: 400 });
  }

  // Delete multiple users in one go
  // Note: We use a placeholder string like (?,?,?) based on array length
  const placeholders = ids.map(() => '?').join(',');
  const sql = `DELETE FROM users WHERE id IN (${placeholders})`;

  await query(sql, ids);

  return NextResponse.json({ success: true });
}
"""
}

def update_api():
    print("🚀 Creating Bulk Delete API...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created: {path}")

if __name__ == "__main__":
    update_api()