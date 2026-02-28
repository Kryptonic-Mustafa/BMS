import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  const loans = await query(`
    SELECT l.*, u.name, u.email, a.account_number
    FROM loans l
    JOIN users u ON l.user_id = u.id
    LEFT JOIN accounts a ON u.id = a.user_id
    ORDER BY l.created_at DESC
  `);
  
  return NextResponse.json(loans);
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session || !session.permissions?.includes('LoansManage') && session.role !== 'admin') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }

  const { loanId, action, comment } = await request.json();
  const status = action === 'approve' ? 'approved' : 'rejected';

  // 1. Get Loan Details
  const loan: any = await query('SELECT * FROM loans WHERE id = ?', [loanId]);
  if (!loan.length) return NextResponse.json({ error: 'Loan not found' }, { status: 404 });
  const loanData = loan[0];

  // 2. Process Approval
  if (status === 'approved') {
      const acc: any = await query('SELECT id FROM accounts WHERE user_id = ? LIMIT 1', [loanData.user_id]);
      if (acc.length > 0) {
          await query('UPDATE accounts SET balance = balance + ? WHERE id = ?', [loanData.amount, acc[0].id]);
          await query('INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "credit", ?, "completed", ?)',
             [acc[0].id, loanData.amount, `Loan Disbursement: #${loanId}`]
          );
      }
  }

  // 3. Update Loan with Comment
  await query('UPDATE loans SET status = ?, approved_by = ?, admin_comment = ? WHERE id = ?', 
    [status, session.id, comment, loanId]);

  // 4. Detailed Notification for User
  const msgTitle = status === 'approved' ? 'Loan Approved! 🎉' : 'Loan Rejected ⚠️';
  const msgBody = status === 'approved' 
    ? `Your loan of $${Number(loanData.amount).toLocaleString()} has been disbursed. Note: ${comment}`
    : `Your loan application was rejected. Reason: ${comment}`;

  await query(
      'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
      [loanData.user_id, `${msgTitle} ${msgBody}`, status === 'approved' ? 'success' : 'error']
  );

  // 5. Audit Log
  await logActivity({
      actorId: session.id,
      actorName: session.name,
      targetId: loanData.user_id,
      action: 'LOAN_DECISION',
      details: `Loan #${loanId} ${status}. Note: ${comment}`
  });

  return NextResponse.json({ success: true });
}