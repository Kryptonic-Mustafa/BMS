import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { searchParams } = new URL(request.url);
  const type = searchParams.get('type') || 'inbox'; 

  let sql = '';
  // Include attachment column
  if (type === 'inbox') {
    sql = `
      SELECT m.*, u.name as sender_name, u.email as sender_email 
      FROM messages m 
      JOIN users u ON m.sender_id = u.id 
      WHERE m.receiver_id = ? 
      ORDER BY m.created_at DESC`;
  } else {
    sql = `
      SELECT m.*, u.name as receiver_name, u.email as receiver_email 
      FROM messages m 
      JOIN users u ON m.receiver_id = u.id 
      WHERE m.sender_id = ? 
      ORDER BY m.created_at DESC`;
  }

  const messages = await query(sql, [session.id]);
  return NextResponse.json(messages);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { to, subject, body, attachment } = await request.json();

  // 'to' is now an array of emails or a single email string
  const emails = Array.isArray(to) ? to : [to];

  for (const email of emails) {
    const receivers: any = await query('SELECT id FROM users WHERE email = ?', [email]);
    if (receivers.length > 0) {
        const receiverId = receivers[0].id;
        
        await query(
            'INSERT INTO messages (sender_id, receiver_id, subject, body, attachment) VALUES (?, ?, ?, ?, ?)',
            [session.id, receiverId, subject, body, attachment || null]
        );

        await query(
            'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
            [receiverId, `New Message: ${subject}`, 'info']
        );
    }
  }

  return NextResponse.json({ success: true });
}