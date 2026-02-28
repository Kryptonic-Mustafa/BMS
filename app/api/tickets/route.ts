import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  let sql = 'SELECT t.*, u.name as user_name, u.email as user_email FROM support_tickets t JOIN users u ON t.user_id = u.id';
  const params = [];

  // FIX: Allow both 'admin' AND 'manager' to see all tickets
  if (!['admin', 'manager'].includes(session.role)) {
    sql += ' WHERE t.user_id = ?';
    params.push(session.id);
  }
  
  sql += ' ORDER BY t.created_at DESC';

  const tickets = await query(sql, params);
  return NextResponse.json(tickets);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const body = await request.json();

  // FIX: Allow Managers to reply too
  if (body.action === 'reply' && ['admin', 'manager'].includes(session.role)) {
    await query('UPDATE support_tickets SET admin_reply = ?, status = ? WHERE id = ?', 
      [body.reply, 'resolved', body.ticketId]);
    return NextResponse.json({ success: true });
  } else {
    await query('INSERT INTO support_tickets (user_id, subject, message, attachment) VALUES (?, ?, ?, ?)', 
      [session.id, body.subject, body.message, body.attachment || null]);
    return NextResponse.json({ success: true });
  }
}