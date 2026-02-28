import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const session = await getSession();
    
    // Security Check
    if (!session || (session.role !== 'admin' && session.role !== 'SuperAdmin' && !session.permissions?.includes('DashboardView'))) {
        return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    // 1. Get Total Customers
    const customers: any = await query(`
        SELECT COUNT(*) as count FROM users 
        WHERE role_id = (SELECT id FROM roles WHERE name = 'Customer' LIMIT 1)
    `);
    
    // 2. Get Total Holdings
    const holdings: any = await query(`SELECT SUM(balance) as total FROM accounts`);
    
    // 3. Get Total Transactions
    const tx: any = await query(`SELECT COUNT(*) as count FROM transactions`);
    
    // 4. Get Live Activity Logs
    // THE FIX: Added ': any' to prevent strict array type-checking conflicts
    let logs: any = [];
    try {
        logs = await query(`SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 15`);
    } catch (e) {
        console.warn("Audit logs table might be missing or empty.", e);
    }

    // Return the formatted data
    return NextResponse.json({
        customers: customers[0]?.count || 0,
        holdings: holdings[0]?.total || 0,
        transactions: tx[0]?.count || 0,
        logs: logs
    });

  } catch (error) {
    console.error("Dashboard API Error:", error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}