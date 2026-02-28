import os

files = {
    # --- FIX 1: Correct the import path ---
    "app/api/users/search/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session'; // FIXED: Imported from session, not auth

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  
  const { searchParams } = new URL(request.url);
  const q = searchParams.get('q') || '';
  
  const users = await query(
    'SELECT id, name, email FROM users WHERE name LIKE ? OR email LIKE ? LIMIT 10', 
    [`%${q}%`, `%${q}%`]
  );
  return NextResponse.json(users);
}
""",

    # --- FIX 2: Re-apply the Database Pool Export ---
    "lib/db.ts": """
import mysql from 'mysql2/promise';

// FIXED: Added 'export' so the Danger Reset route can use it for transactions
export const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  port: parseInt(process.env.DB_PORT || '4000'),
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  ssl: {
    minVersion: 'TLSv1.2',
    rejectUnauthorized: true
  }
});

export async function query(sql: string, values: any[] = []) {
  const [results] = await pool.execute(sql, values);
  return results;
}
"""
}

def fix_vercel_build():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Fixed Vercel Build Errors (Imports & DB Pool)!")

if __name__ == "__main__":
    fix_vercel_build()