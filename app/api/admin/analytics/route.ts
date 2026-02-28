import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
      const session = await getSession();
      if (!session || (session.role !== 'admin' && session.role !== 'SuperAdmin' && !session.permissions?.includes('Reports'))) {
          return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
      }

      // 1. Transaction Volume (REAL DATA: Groups existing transactions by date)
      const rawTx: any = await query(`
          SELECT 
              DATE_FORMAT(created_at, '%b %d') as date,
              SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END) as credits,
              SUM(CASE WHEN type = 'debit' THEN amount ELSE 0 END) as debits
          FROM transactions
          GROUP BY DATE(created_at), DATE_FORMAT(created_at, '%b %d')
          ORDER BY DATE(created_at) ASC
          LIMIT 30
      `);

      const txData = rawTx.map((row: any) => ({
          date: row.date,
          credits: Number(row.credits || 0),
          debits: Number(row.debits || 0)
      }));

      // 2. User Growth Data (REAL DATA: Safe Grouping)
      const rawUsers: any = await query(`
          SELECT DATE_FORMAT(created_at, '%b %Y') as month, COUNT(*) as users
          FROM users
          WHERE role_id = (SELECT id FROM roles WHERE name='Customer' LIMIT 1)
          GROUP BY DATE_FORMAT(created_at, '%b %Y')
          ORDER BY MIN(created_at) ASC 
          LIMIT 6
      `);
      const userGrowth = rawUsers.map((row: any) => ({ month: row.month, users: Number(row.users) }));

      // 3. Transaction Distribution (Credits vs Debits count - Guaranteed to work)
      const rawTxDist: any = await query(`
          SELECT UPPER(type) as name, COUNT(*) as value
          FROM transactions
          GROUP BY type
      `);
      const accountDist = rawTxDist.map((row: any) => ({ 
          name: row.name, 
          value: Number(row.value) 
      }));

      return NextResponse.json({ txData, userGrowth, accountDist });
  } catch (error: any) {
      console.error('Analytics API Error:', error);
      // Send the actual error message to the frontend so we know what went wrong
      return NextResponse.json({ error: error.message || 'Failed to fetch analytics' }, { status: 500 });
  }
}