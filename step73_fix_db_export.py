import os

files = {
    "lib/db.ts": """
import mysql from 'mysql2/promise';

// THE FIX: Added 'export' so other files can use the raw pool for transactions
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

def fix_db_export():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Fixed lib/db.ts! The 'pool' is now exported for Vercel.")

if __name__ == "__main__":
    fix_db_export()