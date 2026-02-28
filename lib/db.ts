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