import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  // Get Pending Requests
  const requests = await query(`
    SELECT k.id, k.document_type, k.document_number, k.file_data, k.submitted_at, 
           u.id as user_id, u.name, u.email 
    FROM kyc_documents k
    JOIN users u ON k.user_id = u.id
    WHERE u.kyc_status = 'pending'
    ORDER BY k.submitted_at DESC
  `);
  
  // Also fetch Audit History for this page (Recent Activity)
  const history = await query(`
    SELECT * FROM audit_logs 
    WHERE action_type IN ('KYC_APPROVE', 'KYC_REJECT') 
    ORDER BY created_at DESC LIMIT 5
  `);

  return NextResponse.json({ requests, history });
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const { userId, action, notes } = await request.json();
  const status = action === 'approve' ? 'verified' : 'rejected';

  // 1. Get Target User Name for logging
  const target: any = await query('SELECT name FROM users WHERE id = ?', [userId]);
  const targetName = target[0]?.name || 'Unknown';

  // 2. Update Status
  await query('UPDATE users SET kyc_status = ? WHERE id = ?', [status, userId]);
  
  // 3. AUDIT LOG
  await logActivity({
    actorId: session.id,
    actorName: session.name,
    targetId: userId,
    targetName: targetName,
    action: action === 'approve' ? 'KYC_APPROVE' : 'KYC_REJECT',
    details: `KYC verification ${action}d. ${notes ? 'Reason: ' + notes : ''}`
  });

  return NextResponse.json({ success: true });
}