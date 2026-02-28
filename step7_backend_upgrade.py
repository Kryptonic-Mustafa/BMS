import os

files = {
    # --- 1. ADMIN: MANAGE USERS (Edit / Delete) ---
    "app/api/admin/users/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

// DELETE USER
export async function DELETE(request: Request) {
  const session = await getSession();
  if (!session || session.role !== 'admin') return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });

  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');

  if (!id) return NextResponse.json({ error: 'ID required' }, { status: 400 });

  // Delete user (Cascade will remove accounts/transactions)
  await query('DELETE FROM users WHERE id = ?', [id]);
  return NextResponse.json({ success: true });
}

// EDIT USER
export async function PUT(request: Request) {
  const session = await getSession();
  if (!session || session.role !== 'admin') return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });

  const body = await request.json();
  const { id, name, email } = body;

  await query('UPDATE users SET name = ?, email = ? WHERE id = ?', [name, email, id]);
  return NextResponse.json({ success: true });
}
""",

    # --- 2. SUPPORT TICKETS API ---
    "app/api/tickets/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

// GET TICKETS (Admin sees all, User sees theirs)
export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  let sql = 'SELECT t.*, u.name as user_name, u.email as user_email FROM support_tickets t JOIN users u ON t.user_id = u.id';
  const params = [];

  if (session.role !== 'admin') {
    sql += ' WHERE t.user_id = ?';
    params.push(session.id);
  }
  
  sql += ' ORDER BY t.created_at DESC';

  const tickets = await query(sql, params);
  return NextResponse.json(tickets);
}

// CREATE TICKET (User) or REPLY (Admin)
export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const body = await request.json();

  if (body.action === 'reply' && session.role === 'admin') {
    // Admin Reply
    await query('UPDATE support_tickets SET admin_reply = ?, status = ? WHERE id = ?', 
      [body.reply, 'resolved', body.ticketId]);
      
    // Optional: Send Email Notification to User about reply (Simulated)
    return NextResponse.json({ success: true });
  } else {
    // New Ticket
    await query('INSERT INTO support_tickets (user_id, subject, message) VALUES (?, ?, ?)', 
      [session.id, body.subject, body.message]);
    return NextResponse.json({ success: true });
  }
}
""",

    # --- 3. BANK MAIL API (Gmail Clone) ---
    "app/api/messages/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { searchParams } = new URL(request.url);
  const type = searchParams.get('type') || 'inbox'; // inbox or sent

  let sql = '';
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

  const { to, subject, body } = await request.json();

  // Find receiver by email
  const receivers: any = await query('SELECT id FROM users WHERE email = ?', [to]);
  if (receivers.length === 0) {
    return NextResponse.json({ error: 'User not found' }, { status: 404 });
  }

  const receiverId = receivers[0].id;

  await query(
    'INSERT INTO messages (sender_id, receiver_id, subject, body) VALUES (?, ?, ?, ?)',
    [session.id, receiverId, subject, body]
  );

  // Notify receiver (Add to notifications table)
  await query(
    'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
    [receiverId, `New Message: ${subject}`, 'info']
  );

  return NextResponse.json({ success: true });
}
"""
}

def upgrade_backend():
    print("🚀 Upgrading Backend: Adding Mail & Support APIs...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created: {path}")
    
    print("\n Backend Upgrade Complete!")

if __name__ == "__main__":
    upgrade_backend()