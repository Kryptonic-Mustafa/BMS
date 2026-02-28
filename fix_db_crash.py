import os

files = {
    "lib/db.ts": """
import mysql from 'mysql2/promise';

// Create a connection pool
export const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
});

export async function query(sql: string, params: any[] = []) {
  try {
    // FIX: Using pool.query() instead of pool.execute() 
    // This fixes the "Incorrect arguments to mysqld_stmt_execute" error
    // caused by LIMIT/OFFSET parameters in prepared statements.
    const [results] = await pool.query(sql, params);
    return results;
  } catch (error) {
    console.error('Database Error:', error);
    throw new Error('Database query failed');
  }
}
"""
}

def fix_db():
    print("🔧 Fixing Database Connection (Switching to pool.query)...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n🚀 Fix applied! Restart your server.")

if __name__ == "__main__":
    fix_db()