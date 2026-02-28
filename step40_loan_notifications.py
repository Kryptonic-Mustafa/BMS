import os

files = {
    "app/api/customer/loans/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  const loans = await query('SELECT * FROM loans WHERE user_id = ? ORDER BY created_at DESC', [session.id]);
  return NextResponse.json(loans);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { amount, duration, purpose, emi, rate } = await request.json();

  // 1. Create Loan
  const res: any = await query(
    'INSERT INTO loans (user_id, amount, duration_months, interest_rate, monthly_emi, purpose) VALUES (?, ?, ?, ?, ?, ?)',
    [session.id, amount, duration, rate, emi, purpose]
  );
  
  // 2. AUDIT LOG (For Dashboard Live Activity)
  await logActivity({
    actorId: session.id,
    actorName: session.name,
    action: 'LOAN_APPLY',
    details: `Applied for loan of $${Number(amount).toLocaleString()} for ${duration} months`
  });

  // 3. NOTIFY ADMINS (Bell Icon)
  // Find all Managers and SuperAdmins
  const admins: any = await query("SELECT id FROM users WHERE role IN ('admin', 'manager')");
  
  for (const admin of admins) {
      await query(
          'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
          [admin.id, `New Loan Request: ${session.name} applied for $${Number(amount).toLocaleString()}`, 'info']
      );
  }

  return NextResponse.json({ success: true });
}
"""
}

def connect_loan_notifications():
    print("🔔 Connecting Loans to Notification System & Audit Logs...")
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    connect_loan_notifications()